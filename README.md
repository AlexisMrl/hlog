# hlog
Application pyqt pour visualiser les données pyHegel et hdf5.


# Structure du code
`hlog.py`:
  - créer l'application pyqt.
  - ordonnance les tâches:
    - thread de chargement des données
    - envoie des données chargées aux `vues` (`views`)
  - garde en mémoire les `vues`

`src/`:
  - contient la définition des objets utile du projet
  - `ReadfileData.py`:
    - gère l'abstraction des données chargées

`views/`:
  - Objets traitant les données charger (objets `rfdata`)
  - `MainView.py`: la fenêtre principale de l'application. Elle reçoit le signal sortant de `hlog.py`: `sig_fileOpened`.

`widgets/`:
  - Fichiers définissant des objets à utiliser dans les vues.
  - Ces fichiers ne connaissent pas le but de l'application. Ils doivent rester le plus général possible.