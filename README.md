# Freebox Connect - Home Assistant Integration

Intégration HACS pour contrôler votre Freebox via Home Assistant, basée sur l'analyse de l'API utilisée par l'application mobile Freebox Connect.


## 💰 Soutenir le Projet

Si cette intégration vous est utile, vous pouvez soutenir son développement avec un don en Bitcoin :

**🪙 Adresse Bitcoin :** `bc1qhe4ge22x0anuyeg0fmts6rdmz3t735dnqwt3p7`

Vos contributions m'aident à continuer d'améliorer ce projet et à ajouter de nouvelles fonctionnalités. Merci ! 🙏

## Installation

### Via HACS (recommandé)

1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points en haut à droite → "Dépôts personnalisés"
4. Ajoutez l'URL : `https://github.com/foXaCe/Freebox-connect`
5. Sélectionnez la catégorie "Intégration"
6. Cliquez sur "Ajouter"
7. Recherchez "Freebox Connect" et installez
8. Redémarrez Home Assistant

### Installation manuelle

1. Téléchargez ce dépôt
2. Copiez le dossier `custom_components/freebox_connect` dans `<config>/custom_components/`
3. Redémarrez Home Assistant

## Configuration

### Étape 1 : Ajouter l'intégration dans Home Assistant

1. Allez dans **Paramètres** → **Appareils et services**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez "Freebox Connect"
4. Entrez le nom d'hôte de votre Freebox (ex: `xxxxxxxx.fbxos.fr`)
5. Entrez le port (par défaut: `46535`)
6. Validez l'accès en appuyant sur la flèche lumineuse de votre Freebox

### Étape 2 : Activer les permissions (IMPORTANT !)

⚠️ **Sans cette étape, certaines fonctionnalités (comme le contrôle des LEDs des répéteurs, WiFi, redémarrage, etc.) ne fonctionneront pas.**

Après avoir configuré l'intégration :

1. Ouvrez votre navigateur et allez sur **[http://mafreebox.freebox.fr/](http://mafreebox.freebox.fr/)**
2. Connectez-vous avec votre compte Freebox
3. Allez dans **Paramètres de la Freebox** → **Gestion des accès**
4. Recherchez l'application **"Home Assistant Freebox Connect"**
5. Cliquez dessus et activez **tous les droits de gestion** :
   - ✅ Modification des réglages de la Freebox
   - ✅ Gestion du système Freebox
   - ✅ Gestion des appareils réseau
   - ✅ Gestion du WiFi
   - etc.
6. Enregistrez les modifications

> 💡 **Astuce** : Si certaines fonctionnalités (switches, boutons) ne fonctionnent toujours pas, vérifiez que tous les droits sont bien activés dans la gestion des accès.

## Stockage des Données

### Token d'Authentification

Le token d'authentification (`app_token`) est stocké de manière sécurisée par Home Assistant dans :

```
<config_directory>/.storage/core.config_entries
```

**Sécurité :**
- ✅ Fichier protégé par permissions système (accessible uniquement par l'utilisateur Home Assistant)
- ✅ Inclus automatiquement dans les sauvegardes Home Assistant
- ℹ️ Token stocké en clair dans le fichier (protection par permissions uniquement)
- ⚠️ Ne jamais partager ce fichier ou votre token

**Format de stockage :**
```json
{
  "entry_id": "...",
  "domain": "freebox_connect",
  "title": "Freebox Ultra",
  "data": {
    "host": "xxxxxxxx.fbxos.fr",
    "port": 46535,
    "app_token": "votre_token_secret",
    "use_https": true
  }
}
```

## Fonctionnalités

### Capteurs disponibles

- **Connection Status** : État de la connexion Internet
  - Attributs : `type`, `media`, `ipv4`, `ipv6`, `rate_down`, `rate_up`
- **Uptime** : Temps de fonctionnement de la Freebox
  - Attributs : `serial`, `firmware`, `mac`, `model`, `uptime_seconds`
- **WiFi State** : État de l'activation WiFi
  - Attributs : `power_saving`, `detected_bands`
- **Storage** : Informations de stockage
  - Attributs : `disks` (liste des disques avec nom, type, capacité)

### Boutons disponibles

- **Reboot** : Redémarrage de la Freebox
- **WiFi Reset** : Réinitialisation de la configuration WiFi

### Répéteurs WiFi

**Capteurs :**
- **Signal Quality** : Qualité du signal (%)
  - Attributs : `state`, `connected_devices`, `name`, `mac`, `model`, `rssi`, `link_quality`
- **State** : État du répéteur
  - Attributs : `name`, `signal_quality`, `connected_devices`, `mac`, `model`, `uptime`
- **Uptime** : Temps de fonctionnement
  - Attributs : `uptime_seconds`, `state`, `name`, `firmware`, `mac`, `model`, `serial`
- **Connected Devices** : Nombre d'appareils connectés
  - Attributs : `name`, `state`, `signal_quality`, `mac`, `model`

**Switches :**
- **LED Indicator** : Contrôler le voyant lumineux

**Boutons :**
- **Reboot** : Redémarrer le répéteur
- **Identify** : Faire clignoter la LED pour localiser le répéteur

### Suivi des appareils

- **Device Tracker** : Suivi des appareils connectés au réseau local

#### Attributs disponibles pour chaque appareil :

- `ip_address` : Adresse IP principale (IPv4 en priorité, IPv6 en fallback)
- `mac_address` : Adresse MAC de l'appareil
- `vendor` : Fabricant de l'appareil
- `interface` : Interface de connexion (wifi, ethernet, etc.)
- `last_seen` : Dernière fois que l'appareil a été vu
- `access_point` : Point d'accès auquel l'appareil est connecté
- `ipv4_addresses` : Liste de toutes les adresses IPv4
- `ipv6_addresses` : Liste de toutes les adresses IPv6
- `connection_type` : Type de connexion (ethernet, wifi, etc.)

## API Freebox

Cette intégration utilise l'API locale de la Freebox. Endpoints principaux :

```
GET  /api_version                    - Version de l'API
POST /api/v15/login/session/         - Authentification
GET  /api/v11/system/                - Infos système
GET  /api/v13/wifi/ap/               - Points d'accès WiFi
GET  /api/v11/connection/            - État connexion
GET  /api/v11/storage/disk/          - Disques
GET  /api/v11/call/log/              - Journal d'appels
```

---

# Guide de développement - Capture de trafic

Pour contribuer au développement ou analyser l'API Freebox Connect :

## Prérequis

- **mitmproxy** installé sur votre PC
- Tablette/smartphone Android
- PC et Android sur le même réseau WiFi

## Configuration proxy

### 1. Démarrer le proxy mitmproxy

Sur votre PC, démarrez mitmdump avec l'option `--ssl-insecure` pour gérer les certificats auto-signés de la Freebox :

```bash
mitmdump --listen-host 0.0.0.0 --listen-port 8080 --ssl-insecure
```

Le proxy écoute maintenant sur toutes les interfaces réseau sur le port 8080.

### 2. Identifier l'adresse IP de votre PC

```bash
ip addr show | grep -E "inet.*/(24|16)" | grep -v "127.0.0.1"
```

Exemple de sortie : `192.168.1.180/24`

### 3. Configurer le proxy sur Android

1. **Paramètres** → **WiFi**
2. Appui long sur votre réseau WiFi → **Modifier**
3. **Options avancées** → **Proxy** : **Manuel**
4. Renseignez :
   - **Nom d'hôte** : l'IP de votre PC (ex: `192.168.1.180`)
   - **Port** : `8080`
5. **Enregistrer**

### 4. Installer le certificat mitmproxy

Pour intercepter le trafic HTTPS, Android doit faire confiance au certificat mitmproxy :

1. Ouvrez un navigateur sur votre tablette
2. Allez sur **http://mitm.it**
3. Téléchargez le certificat pour Android
4. Installez-le :
   - **Paramètres** → **Sécurité** → **Certificats** → **Installer depuis le stockage**
   - Sélectionnez le certificat téléchargé
   - Donnez-lui un nom (ex: "mitmproxy")

### 5. Lancer Freebox Connect

Lancez l'application Freebox Connect. Le trafic apparaît maintenant dans votre terminal mitmdump !

## Requêtes capturées

L'app utilise l'API locale de la Freebox via HTTPS :

```
POST https://xxxxxxxx.fbxos.fr:46535/api/v15/login/session/
GET  https://xxxxxxxx.fbxos.fr:46535/api/v11/system/
GET  https://xxxxxxxx.fbxos.fr:46535/api/v11/login/perms/
```

Le domaine `*.fbxos.fr` pointe vers votre Freebox locale (IPv6/IPv4).

## Commandes utiles

### Sauvegarder la capture dans un fichier

```bash
mitmdump --listen-host 0.0.0.0 --listen-port 8080 --ssl-insecure -w capture.mitm
```

### Filtrer uniquement les requêtes vers la Freebox

```bash
mitmdump --listen-host 0.0.0.0 --listen-port 8080 --ssl-insecure --flow-filter "~d fbxos.fr"
```

### Rejouer une capture

```bash
mitmdump -r capture.mitm
```

### Exporter en format HAR (HTTP Archive)

```bash
mitmdump -r capture.mitm --set hardump=capture.har
```

## Dépannage

### L'app refuse de se connecter

- Vérifiez que le certificat mitmproxy est bien installé sur Android
- Assurez-vous d'utiliser l'option `--ssl-insecure` (nécessaire pour les certificats auto-signés de la Freebox)

### Pas de trafic visible

- Vérifiez la configuration du proxy sur Android
- Testez avec un navigateur : allez sur http://mitm.it (doit afficher la page d'accueil mitmproxy)
- Vérifiez que le pare-feu autorise les connexions sur le port 8080

### Erreurs de certificat

```
Certificate verify failed: unable to get local issuer certificate
```

→ Relancez mitmdump avec l'option `--ssl-insecure`

## Désactivation

Pour désactiver le proxy après analyse :

1. **Android** : Paramètres WiFi → Proxy : **Aucun**
2. **PC** : Arrêtez mitmdump avec `Ctrl+C`

## Notes

- Le certificat mitmproxy permet l'interception HTTPS man-in-the-middle
- Utilisez uniquement à des fins de développement/débogage
- Ne laissez pas le proxy configuré en permanence sur Android

---

## Développement

### Qualité du code

Ce projet utilise [Ruff](https://docs.astral.sh/ruff/) pour le linting et le formatage du code Python.

#### Installation des outils de développement

```bash
# Installer Ruff
pip install ruff

# Installer pre-commit
pip install pre-commit
pre-commit install
```

#### Commandes disponibles

```bash
# Linting (vérifier le code)
ruff check .

# Linting avec auto-correction
ruff check --fix .

# Formatage du code
ruff format .

# Vérifier le formatage sans modifier
ruff format --check .

# Lancer tous les hooks pre-commit manuellement
pre-commit run --all-files
```

#### Pre-commit hooks

Les hooks pre-commit sont configurés pour s'exécuter automatiquement avant chaque commit :
- Ruff linter avec auto-correction
- Ruff formatter
- Vérifications de base (trailing whitespace, end-of-file, etc.)
- Codespell pour corriger les fautes de frappe

#### CI/CD

Les workflows GitHub Actions vérifient automatiquement la qualité du code sur chaque push et pull request.

## Licence

MIT License - Voir le fichier LICENSE pour plus de détails.
