# hlog
Application pyqt pour visualiser les données pyHegel et hdf5.


# Structure du code
`hlog.py`:
  - créer l'application pyqt.
  - ordonnance les tâches:
    - thread de chargement des données
    - envoie des données chargées à `MainView`

`src/`:
  - contient la définition des objets utile du projet
  - `ReadfileData.py`:
    - gère l'abstraction des données chargées

`views/`:
  - `MainView`:
    - garde en mémoire les `vues`
    - gère les fenêtres/`widgets` de l'application

`widgets/`:
  - Fichiers définissant des objets à utiliser dans les vues
