let data = document.getElementById('printContent');
let btn= document.getElementById('printTable');



function tablePrint() {
    window.print();
}

btn.addEventListener('click',tablePrint)

