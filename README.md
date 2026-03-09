

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
		 uv run plot_false_color_luminance
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

Le tonemapping bilatéral (Durand & Dorsey) repose sur plusieurs paramètres :

- **sigma_spatial** : contrôle le lissage spatial lors du filtrage bilatéral. Plus la valeur est élevée, plus le lissage est fort, ce qui réduit les détails locaux.
- **sigma_range** : contrôle le lissage en intensité (dans l'espace des valeurs de luminance). Une valeur élevée permet de mieux préserver les transitions d’intensité.
- **desired_contrast** : définit le contraste final de l’image LDR. Plus ce paramètre est faible, plus l’image sera compressée en dynamique.
- **nb_segments** : nombre de segments utilisés pour l’approximation du filtre bilatéral (par défaut 16). Influence la finesse de l’approximation.
- **downsample_factor** : facteur de sous-échantillonnage pour accélérer le filtrage (par défaut 2).

L’algorithme procède en plusieurs étapes, toutes rassemblées dans la fonction `bilateral_tone_mapping` :
1. Calcul de la luminance à partir de l’image HDR (`compute_luminance`)
2. Passage en log-luminance
3. Filtrage bilatéral pour séparer la couche de base (lissée) et la couche de détail (`compute_base_layer`)
4. Compression de la couche de base selon le contraste désiré (`compress_base_layer`)
5. Reconstruction de l’image LDR, normalisation et correction gamma

Vous pouvez ajuster les paramètres pour obtenir le rendu souhaité selon vos images HDR.
