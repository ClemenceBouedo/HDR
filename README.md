

# HDR

Ce projet permet de manipuler et traiter des images à grande gamme dynamique (HDR) à partir de séquences d’images classiques (PNG ou JPG).

Il a été initialisé avec le template [supopo-pai-cookiecutter-template](https://github.com/ClementPinard/supop-pai-cookiecuttter-template/tree/main).

### Généralités

L’imagerie HDR vise à capturer et restituer toute la dynamique lumineuse d’une scène, là où une image classique ne peut représenter que des valeurs limitées. Ce projet propose des outils pour créer des fichiers HDR à partir de photos prises avec différents temps d’exposition, puis pour les convertir en images LDR (Low Dynamic Range) affichables tout en préservant les détails.

## Mode d'emploi

Voici les principales étapes pour utiliser ce projet :

1. **Réduction de taille des images**
	 - Utilisez le script `reduce_images.py` pour réduire la taille des images sources (PNG ou JPG) si nécessaire.
	- Un fichier texte contenant les temps d'exposition est créé lors de la conversion de JPG en PNG.
	 - Paramétrez le dossier source, le dossier de destination, le facteur de réduction et le format de sortie en haut du script.
	 - Lancez la commande :
		 ```bash
		 uv run reduce_images
		 ```

2. **Création du fichier HDR**
	 - Utilisez le script `create_hdr.py` pour générer le fichier HDR à partir des images réduites et du fichier des temps d’exposition (si images PNG)
	 - Adaptez les paramètres en haut du script selon votre séquence.
	 - Lancez la commande :
		 ```bash
		 uv run create_hdr
		 ```

3. **Visualisation en fausses couleurs**
	 - Le script `plot_false_color_luminance.py` permet d’afficher et sauvegarder une carte de luminance en fausses couleurs (échelle log10, colormap personnalisable).
	 - Modifiez les chemins et paramètres en haut du script.
	 - Lancez la commande :
		 ```bash
		 uv run false_color
		 ```

4. **Tonemapping (conversion HDR → LDR)**
	 - Utilisez le script `tonemapping.py` pour convertir le fichier HDR en image LDR affichable.
	 - Les paramètres du tone mapping (sigma_spatial, sigma_range, desired_contrast, etc.) sont en haut du script.
	 - Lancez la commande :
		 ```bash
		 uv run tonemapping
		 ```

Chaque script peut être adapté en modifiant les paramètres en haut du fichier. Les chemins sont calculés automatiquement à partir de la racine du projet.

---

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