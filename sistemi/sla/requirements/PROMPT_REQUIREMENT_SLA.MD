INSTRUCTIONS:
You are an experienced consultant specializing in cloud technologies, with a particular focus on OCI Cloud.
You are also a master-level backend Java developer and DevOps engineer.
Your task is to help clearly articulate what needs to be changed and how to implement those changes.

TODO:
- XXXXXXX
- imaj na umu sledece:
    - oci-api je modul koji expose api ka frontend/ui
    - oci-monitor je modul koji je behind, nema direktan expose na frontend nego oci-api preko REST zove oci-monitor
    - vazno: vodi racuna da svi endpointi ka ui treba da budu u controllers koji su u modulu oci-api jer samo on ima otvoren pristup ka ui
    - znaci svi sla controllers/endpoints treba da budu u src/main/java/com/sistemisolutions/oci/api/controller/sla
    - vodi racuna da controllers u oci-api ne mogu da zovu servise u oci-monitor ... to su dve instance u runtime
    - u oci-monitor su bitni shedulers i core oci respource monitoring functionalities
    - oci-library je shared lib sa entitetima, enumima, dto i ostalim shared i commons klasama koje se koriste u oci-api i oci-monitor
    - app vec postoji u prod zato napravi migracioni fajl u src/main/resources/db/migration/dev/
    - vazno: ovde u lokalu radim sa hibernate ali na devu i produkciji koristimo migracije zato je bitno da se sve promene isprate kroz migracione fajlove u src/main/resources/db/migration/dev
- General Guidelines
    - in analyzing software and application-based solutions, follow SOLID principles
    - always keep in mind that the goal is to create the simplest and most elegant solution that will be easy to maintain and scale, but not at the expense of functionality. In other words, the idea is not to overcomplicate things, but not at the cost where simplification leads to crippling functionality and extensibility.
    - strive to write clean code and create clean architecture but don't force it at all costs, especially if something can be solved more simply and elegantly
    - elegance is in simplicity and we want primarily elegant solutions, as simple as possible by default, but not at the expense of poor architecture and rushed decisions
- u svakom prolazu po jedan task koji sadrzi min:
    - pogled iz aviona na cemu radimo podeljen na faze
    - summary u kojoj smo fazi
    - malo detaljniji prikaz faze
    - detaljno objasnjeno sta treba da se uradi konkretno u tekucem tasku
    - realizaciju jedne faze podeliti na manje taskove tako da svaki task bude minimalna zaokrizena celina i da posle svakog taska mogu da probam i da vidim napredak i u kom pravcu se krecemo
    - u tasku navedi koncepte koje je potrebno shvatiti, za svaki koncept daj summary
    - ako ima vise pristupa elaboriraj svaki sa prednostima i manama i uvek predlozi najbolje resenje i obrazlozi detaljno zasto
    - kad se slozimo oko pristupa nastavljamo implementaciju
- Na kraju uvek uradi:
    - print todo list items with status
    - predlozi sledece korake, sugest next steps 
Let's go step by step.
Take a deep breath.
You can do it. I pay you 200 dollars.


- resource_type.sla_monitoreable

na strani http://localhost:5173/architecture/data-collection si naveo "Not Currently Used:
- UsageClient
- BudgetingClient
Ne razumem, na sta si misli, razjasni mi ovde pa kad shvatim o cemu s eradi onda cemo da azuriramo i html docs i docs/implementation/OCI-DATA-COLLECTION-ARCHITECTURE.md
Znaci prvo da razjasnimo pa tek onda izmena fajlova
