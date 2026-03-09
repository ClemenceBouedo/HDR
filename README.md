
## HDR

Ce projet permet de manipuler et traiter des images à grande gamme dynamique (HDR) à partir de séquences d’images classiques (PNG ou JPG). Il a été initialisé avec le template [supopo-pai-cookiecutter-template](https://github.com/ClementPinard/supop-pai-cookiecuttter-template/tree/main).

### Généralités

L’imagerie HDR vise à capturer et restituer toute la dynamique lumineuse d’une scène, là où une image classique ne peut représenter que des valeurs limitées. Ce projet propose des outils pour créer des fichiers HDR à partir de photos prises avec différents temps d’exposition, puis pour les convertir en images LDR (Low Dynamic Range) affichables tout en préservant les détails.

## Création du fichier HDR

La création d’un fichier HDR se fait à partir d’une séquence d’images (PNG ou JPG) et d’un fichier texte listant les temps d’exposition. Le script `create_hdr.py` automatise cette étape :

- Lecture des images et des temps d’exposition
- Calcul des courbes de réponse de la caméra
- Fusion des images pour obtenir une radiance map HDR
- Sauvegarde du fichier HDR au format `.hdr`

Vous pouvez adapter les paramètres (chemins, mode PNG/JPG, nombre de points, etc.) en haut du script pour traiter vos propres séquences.

## Tonemapping

La partie tonemapping du projet permet de convertir une radiance map au format `.hdr` en une image LDR affichable, tout en préservant au mieux les détails et le contraste.

L’algorithme procède en plusieurs étapes, toutes rassemblées dans la fonction `bilateral_tone_mapping`. Le tonemapping bilatéral repose sur plusieurs paramètres(sigma_spatial, sigma_range, desired_contrast), ajustables pour obtenir le rendu souhaité selon vos images HDR.

Chargez d’abord l’image HDR avec la fonction load_hdr_image, comme dans le main(), en modifiant simplement le chemin du fichier dans la variable HDR_PATH. Vous pouvez également ajuster les paramètres du tonemapping (SIGMA_SPATIAL, SIGMA_RANGE, DESIRED_CONTRAST) en haut du script pour modifier le rendu final. Ensuite, exécutez le script : l’image tonemappée sera automatiquement générée et sauvegardée dans le dossier output_final.