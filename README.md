Lai palaistu šo programmu ir jāveic šādi soļi: 
1.	Pārliecinaties vai jūsu sistēmā ir ieienstelēts python ar komandu ‘python -V’ vai arī ar ‘python –version’
2.	Instalējiet virtuālo direktoriju ‘pip install virtualenv’
3.	Izveidojiet virtuālo direktoriju ar komandu ‘virtualenv myenv’
4.	Aktivējiet aktīvo virtuālo direktoriju ‘myenv\Scripts\activate’
5.	Ieienstalējiet vajadzīgās instalācijas priekš projekta ‘pip install -r requirements.txt’
6.	Veiciet datu bāzes migrāciju ar ‘python manage.py migrate’
7.	Django servera palaišana. Serveri var palaist ar komandu ‘python manage.py runserver’, kas veidos piekļuvi vietnei ‘http://127.0.0.1:8000/’ bet ja vēlaties izmantot un palaist serveri uz kāda cita porta tad ar komandu ‘python manage.py runserver 8084’ kas padarīs vietni pieejamu uz ‘http://127.0.0.1:8084/’. attiecīgi mainiet porta numuru kas šeit bija norādīts ‘8084’ kas tad ir ‘python manage.py runserver “porta numurs”  ’. 
