## HDR

This project was started with [supopo-pai-cookiecutter-template](https://github.com/ClementPinard/supop-pai-cookiecuttter-template/tree/main)

## How to run

⚠️ Chose one of the two method below, and remove the other one.

### How to run with NiceGUI

```bash
uv run main_ng
```

You can also run in development mode, which will reload the interface when it see code
changes.

```bash
uv run python HDR/main_nicegui.py
```

### How to run with PySide

```bash
uv run main_qt
```

## Development

### How to run pre-commit

```bash
uvx pre-commit run -a
```

Alternatively, you can install it so that it runs before every commit :

```bash
uvx pre-commit install
```

### How to run tests

```bash
uv sync --group test
uv run coverage run -m pytest -v
```

### How to run type checking

```bash
uvx pyright HDR --pythonpath .venv/bin/python
```

### How to build docs

```bash
uv sync --group docs
cd docs && uv run make html
```

#### How to run autobuild for docs

```bash
uv sync --group docs
cd docs && make livehtml

## Tonemapping

La partie tonemapping du projet permet de convertir une radiance map au format .hdr en une image LDR affichable, tout en préservant au mieux les détails et le contraste.

Le tonemapping bilatéral (Durand & Dorsey) repose sur plusieurs paramètres :

- **sigma_spatial** : contrôle le lissage spatial lors du filtrage bilatéral. Plus la valeur est élevée, plus le lissage est fort, ce qui réduit les détails locaux.
- **sigma_range** : contrôle le lissage en intensité (dans l'espace des valeurs de luminance). Une valeur élevée permet de mieux préserver les transitions d’intensité.
- **desired_contrast** : définit le contraste final de l’image LDR. Plus ce paramètre est faible, plus l’image sera compressée en dynamique.
- **nb_segments** : nombre de segments utilisés pour l’approximation du filtre bilatéral (par défaut 16). Influence la finesse de l’approximation.
- **downsample_factor** : facteur de sous-échantillonnage pour accélérer le filtrage (par défaut 2).

L’algorithme procède en plusieurs étapes, toutes rassemblées dans la fonction "bilateral_tone_mapping" :
1. Calcul de la luminance à partir de l’image HDR (compute_luminance)
2. Passage en log-luminance
3. Filtrage bilatéral pour séparer la couche de base (lissée) et la couche de détail (compute_base_layer)
4. Compression de la couche de base selon le contraste désiré (compress_base_layer)
5. Reconstruction de l’image LDR, normalisation et correction gamma.

Vous pouvez ajuster les paramètres pour obtenir le rendu souhaité selon vos images HDR. 
