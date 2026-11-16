"""PDF 翻译任务服务：把 pdftranslate 的流水线包装成可轮询的后台任务。

- 复用 vendored 的 pdftranslate 包（视觉大模型转写+翻译）
- 任务状态存内存 dict，输出落在 uploads/pdf_translate/<job_id>/out
- 前端轮询 /pdf_translate/status/<job_id> 取进度与产物
"""

from __future__ import annotations

import json
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from pdftranslate import models as registry
from pdftranslate.config import Config
from pdftranslate.pipeline import Options, run_job

BASE_DIR = Path(__file__).resolve().parent
WORK_ROOT = BASE_DIR / 'uploads' / 'pdf_translate'
WORK_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_SUFFIXES = {'.pdf', '.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.bmp'}
MAX_FILE_BYTES = 80 * 1024 * 1024  # 80MB / 文件

_jobs: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()
MAX_JOBS_KEPT = 40


# ---------------- 模型列表 ----------------
def available_models() -> list[dict[str, str]]:
    """返回可用模型（含是否已配置 Key）。"""
    out: list[dict[str, str]] = []
    try:
        entries = registry.entries()
    except Exception:
        entries = []
    for m in entries:
        out.append({
            'id': m.id,
            'label': m.label,
            'note': getattr(m, 'note', '') or '',
            'has_key': bool(getattr(m, 'api_key', '')),
            'proxy': bool(getattr(m, 'proxy', False)),
        })
    return out


def default_model() -> str:
    try:
        return registry.default_id()
    except Exception:
        return 'qwen'


# ---------------- 任务管理 ----------------
def _public(job: dict[str, Any]) -> dict[str, Any]:
    """给前端的状态快照（不含内部路径）。"""
    return {
        'id': job['id'],
        'status': job['status'],          # queued | running | done | failed
        'progress': job['progress'],      # 0-100
        'done_pages': job['done_pages'],
        'total_pages': job['total_pages'],
        'logs': job['logs'][-120:],
        'files': job['files'],            # [{name, pages, failed}] 
        'outputs': job['outputs'],        # [{label, name, size}]
        'error': job['error'],
        'elapsed': round(time.time() - job['started'], 1) if job['started'] else 0,
        'created': job['created_label'],
        'model': job['model'],
        'mock': job['mock'],
    }


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return _public(job) if job else None


def list_jobs() -> list[dict[str, Any]]:
    with _lock:
        jobs = sorted(_jobs.values(), key=lambda j: j['created_ts'], reverse=True)
    return [_public(j) for j in jobs]


def job_dir(job_id: str) -> Path | None:
    job = _jobs.get(job_id)
    return Path(job['workdir']) if job else None


def _prune() -> None:
    if len(_jobs) <= MAX_JOBS_KEPT:
        return
    stale = sorted(_jobs.values(), key=lambda j: j['created_ts'])[: len(_jobs) - MAX_JOBS_KEPT]
    for job in stale:
        _jobs.pop(job['id'], None)
        shutil.rmtree(job['workdir'], ignore_errors=True)


def _scan_outputs(out_dir: Path) -> list[dict[str, Any]]:
    """列出产物（pdf / html / md / zip）。"""
    if not out_dir.is_dir():
        return []
    label_map = {'.pdf': '双语 PDF', '.html': '覆盖式 HTML', '.md': '译文 Markdown', '.zip': '打包下载'}
    outs: list[dict[str, Any]] = []
    for f in sorted(out_dir.rglob('*')):
        if not f.is_file() or f.name.startswith('.'):
            continue
        if f.suffix.lower() not in label_map:
            continue
        outs.append({
            'label': label_map[f.suffix.lower()],
            'name': str(f.relative_to(out_dir)).replace('\\', '/'),
            'size': f.stat().st_size,
        })
    return outs


def create_job(
    *,
    files: list[tuple[str, bytes]],
    model_id: str,
    pages: str = '',
    dpi: int = 250,
    want_pdf: bool = True,
    want_html: bool = True,
    want_md: bool = True,
    text_layer: str = 'auto',
    target_lang: str = '简体中文',
    mock: bool = False,
) -> tuple[str | None, str | None]:
    """保存上传文件并启动后台翻译任务。返回 (job_id, error)。"""
    if not files:
        return None, '请先选择要翻译的 PDF 或图片文件'

    for name, data in files:
        suffix = Path(name).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            return None, f'不支持的文件类型：{name}（仅支持 PDF / PNG / JPG / TIFF / BMP）'
        if len(data) > MAX_FILE_BYTES:
            return None, f'文件过大：{name}（上限 80MB）'

    job_id = time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    workdir = WORK_ROOT / job_id
    src_dir = workdir / 'in'
    out_dir = workdir / 'out'
    src_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for name, data in files:
        safe = Path(name).name.replace('/', '_').replace('\\', '_')
        p = src_dir / safe
        p.write_bytes(data)
        saved.append(p)

    try:
        cfg = Config.from_env(model_id, dpi=max(72, min(int(dpi), 400)), mock=mock)
    except SystemExit as e:            # registry 抛的是 SystemExit
        return None, str(e) or '模型配置错误'

    opts = Options(pages=(pages or '').strip(), pdf=want_pdf, html=want_html, md=want_md,
                   text_layer=text_layer if text_layer in {'auto', 'always', 'never'} else 'auto')

    job: dict[str, Any] = {
        'id': job_id,
        'workdir': str(workdir),
        'status': 'queued',
        'progress': 0,
        'done_pages': 0,
        'total_pages': 0,
        'logs': [f'已接收 {len(saved)} 个文件，模型：{cfg.label or cfg.provider}'],
        'files': [{'name': p.name, 'pages': 0, 'failed': []} for p in saved],
        'outputs': [],
        'error': '',
        'started': 0.0,
        'created_ts': time.time(),
        'created_label': time.strftime('%m-%d %H:%M'),
        'model': cfg.label or cfg.provider,
        'mock': mock,
    }

    with _lock:
        _jobs[job_id] = job
        _prune()

    def emit(line: str) -> None:
        with _lock:
            job['logs'].append(line.rstrip())

    def progress(done: int, total: int) -> None:
        with _lock:
            job['status'] = 'running'
            job['done_pages'] = done
            job['total_pages'] = total
            if total > 0:
                job['progress'] = min(99, int(done * 100 / total))

    def worker() -> None:
        job['started'] = time.time()
        job['status'] = 'running'
        try:
            stats = run_job(saved, cfg, opts, out_dir, emit, progress=progress)
            files_info = []
            for st in stats:
                files_info.append({
                    'name': st.path.name,
                    'pages': st.pages,
                    'ok': st.ok,
                    'failed': st.failed,
                })
            outputs = _scan_outputs(out_dir)
            with _lock:
                job['files'] = files_info
                job['outputs'] = outputs
                job['progress'] = 100
                job['status'] = 'done' if outputs else 'failed'
                if not outputs:
                    job['error'] = '未生成任何产物，请查看日志'
                job['logs'].append(f'完成，用时 {round(time.time() - job["started"], 1)}s，产物 {len(outputs)} 个')
        except Exception as e:  # noqa: BLE001  —— 后台任务需兜底
            with _lock:
                job['status'] = 'failed'
                job['error'] = f'{type(e).__name__}: {e}'
                job['logs'].append('失败：' + job['error'])

    threading.Thread(target=worker, daemon=True, name=f'pdfxlate-{job_id}').start()

    return job_id, None
