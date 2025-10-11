# Freebox Connect - Home Assistant Integration

Intégration HACS pour contrôler votre Freebox via Home Assistant, basée sur l'analyse de l'API utilisée par l'application mobile Freebox Connect.

## Installation

### Via HACS (recommandé)

1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points en haut à droite → "Dépôts personnalisés"
4. Ajoutez l'URL : `https://github.com/your-username/freebox-connect`
5. Sélectionnez la catégorie "Intégration"
6. Cliquez sur "Ajouter"
7. Recherchez "Freebox Connect" et installez
8. Redémarrez Home Assistant

### Installation manuelle

1. Téléchargez ce dépôt
2. Copiez le dossier `custom_components/freebox_connect` dans `<config>/custom_components/`
3. Redémarrez Home Assistant

## Configuration

1. Allez dans **Paramètres** → **Appareils et services**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez "Freebox Connect"
4. Entrez le nom d'hôte de votre Freebox (ex: `5mu9y3pt.fbxos.fr`)
5. Entrez le port (par défaut: `46535`)

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
POST https://5mu9y3pt.fbxos.fr:46535/api/v15/login/session/
GET  https://5mu9y3pt.fbxos.fr:46535/api/v11/system/
GET  https://5mu9y3pt.fbxos.fr:46535/api/v11/login/perms/
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

# Dépannage

## Erreur "Home access is not granted"

Cette erreur provient de l'intégration **officielle** Freebox de Home Assistant.

**Solution :**
1. Connectez-vous à votre interface Freebox : **http://mafreebox.freebox.fr**
2. Allez dans **Paramètres de la Freebox** → **Gestion des accès** → **Applications**
3. Trouvez **"Home Assistant"** dans la liste
4. Cliquez sur **Modifier les permissions**
5. Activez : **"Gestion de l'alarme et maison connectée"**
6. Redémarrez Home Assistant

## WiFi State affiche "disabled" alors qu'il est activé

L'API Freebox peut retourner différentes structures de données selon les modèles.

**Solution :**
1. Vérifiez les logs de Home Assistant pour voir les données brutes :
   ```
   Logger: custom_components.freebox_connect.sensor
   ```
2. Cherchez la ligne avec `WiFi state data: {...}`
3. L'intégration a été mise à jour pour gérer plusieurs formats

Si le problème persiste, utilisez le script de diagnostic :
```bash
python3 test_permissions.py
```

## Boutons repeater affichent "Indisponible"

Les boutons des répéteurs peuvent être indisponibles pour plusieurs raisons.

**Causes possibles :**
1. Le repeater n'est pas présent dans les données de l'API
2. Le coordinator n'a pas réussi à rafraîchir les données
3. Le repeater ID n'est pas valide

**Solution :**
1. Vérifiez les logs Home Assistant pour voir quels repeaters sont détectés :
   ```
   Logger: custom_components.freebox_connect.button
   Found repeater X with state: ...
   Added buttons for repeater X
   ```

2. Utilisez le script de diagnostic :
   ```bash
   python3 test_repeater.py
   ```

3. Vérifiez que le repeater apparaît dans les données de l'API

**Note :** Les boutons sont maintenant créés pour tous les repeaters détectés, quel que soit leur état.

## Repeater reboot ne fonctionne pas

Certains modèles de répéteurs ne supportent pas l'endpoint `/reboot`.

**Comportement normal :**
- Le message `Reboot endpoint not available for repeater X` est normal pour certains modèles
- Seuls les modèles supportant l'API de reboot afficheront un bouton fonctionnel

## Tous les capteurs de répéteur affichent "Inconnu" ou "0"

Si tous les capteurs du répéteur (Signal, État, Uptime, Appareils connectés) affichent "Inconnu" ou "0", le répéteur n'est probablement pas détecté par l'API.

**Causes possibles :**
1. Aucun répéteur WiFi n'est appairé à votre Freebox
2. Le répéteur est hors ligne ou déconnecté
3. L'endpoint `/api/v11/repeater/` n'est pas disponible sur votre modèle de Freebox
4. Permissions API manquantes

**Diagnostic rapide :**

1. **Test de l'endpoint API :**
   ```bash
   python3 test_repeater_quick.py
   ```

   Ce script teste directement l'endpoint et vous indique :
   - ✅ Si des répéteurs sont détectés
   - ⚠️ Si la liste est vide (aucun répéteur)
   - ❌ Si l'endpoint ne répond pas

2. **Vérifier les logs Home Assistant :**

   Activez le mode debug (voir section "Logs utiles") et cherchez :
   ```
   Found X repeater(s)
   Repeater 0: {...}
   ```

   Si vous voyez `No repeater data retrieved from API`, l'endpoint ne retourne rien.

3. **Vérifier sur l'interface Freebox :**

   Allez sur http://mafreebox.freebox.fr → Paramètres → WiFi → Répéteurs

   Si aucun répéteur n'apparaît, c'est normal que Home Assistant n'en détecte pas.

## Signal Quality affiche 0% ou indisponible

Le capteur de qualité du signal peut afficher 0% si le champ de l'API n'est pas trouvé.

**Solution :**
1. Activez les logs de debug (voir section "Logs utiles")
2. Cherchez dans les logs : `No signal data found for repeater X. Available keys: [...]`
3. Utilisez le script de diagnostic spécifique au signal :
   ```bash
   python3 test_repeater_signal.py
   ```

Ce script affiche tous les champs disponibles et identifie automatiquement les champs liés au signal (`signal_quality`, `link_quality`, `signal`, `rssi`, etc.)

## Scripts de diagnostic

Quatre scripts sont fournis pour diagnostiquer les problèmes :

### test_permissions.py
Teste les permissions et endpoints de l'API :

```bash
python3 test_permissions.py
```

Ce script vérifie :
- ✅ Version de l'API
- ✅ Autorisation de l'application
- ✅ Ouverture de session
- ✅ Permissions accordées
- ✅ Disponibilité des endpoints clés

### test_repeater.py
Debug général pour les répéteurs :

```bash
python3 test_repeater.py
```

Ce script affiche :
- 📊 Nombre de repeaters détectés
- 🔍 Données complètes de chaque repeater (ID, state, signal, etc.)
- 📋 Liste de tous les champs disponibles

### test_repeater_quick.py
Test rapide pour vérifier si l'API retourne des répéteurs :

```bash
python3 test_repeater_quick.py
```

Ce script affiche :
- ✅ Si des répéteurs sont détectés (avec résumé)
- ⚠️ Si l'API retourne une liste vide
- ❌ Si l'endpoint ne répond pas
- 📊 Résumé des données (ID, nom, état, signal, etc.)

### test_repeater_signal.py
Debug spécifique pour le signal des répéteurs :

```bash
python3 test_repeater_signal.py
```

Ce script affiche :
- 🔍 Tous les champs liés au signal (signal_quality, rssi, link_quality, etc.)
- ✅/❌ Indique quels champs sont présents ou absents
- 📋 Affichage détaillé de toutes les données du répéteur

## Logs utiles

Pour activer les logs de debug dans Home Assistant, ajoutez dans `configuration.yaml` :

```yaml
logger:
  default: info
  logs:
    custom_components.freebox_connect: debug
```

Puis redémarrez Home Assistant.
