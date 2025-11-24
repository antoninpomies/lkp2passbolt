# Convertisseur Lockpass → Passbolt

Ce script Python convertit un fichier CSV exporté depuis Lockpass vers le format CSV compatible avec Passbolt (format LastPass).

## 📋 Prérequis

- Python 3.6 ou supérieur
- Un fichier CSV exporté depuis Lockpass

## 🚀 Installation

Aucune installation de bibliothèques externes n'est nécessaire. Le script utilise uniquement les modules standards de Python.

**Le script détecte automatiquement l'encodage du fichier** et supporte :
- UTF-8 (avec ou sans BOM)
- UTF-16 (LE/BE)
- Latin-1
- Windows-1252
- ISO-8859-1

**Le fichier de sortie est toujours en UTF-8 avec BOM** pour une compatibilité maximale avec Excel et Passbolt.

📘 **Problèmes d'accents ?** Consultez le [GUIDE_ACCENTS.md](GUIDE_ACCENTS.md)

## 💻 Utilisation

### Fonctionnalités principales

Le script :
- ✅ Détecte automatiquement l'encodage du fichier source
- ✅ Convertit tous les champs (URL, username, password, name, etc.)
- ✅ Préserve les catégories/sous-catégories et les codes TOTP
- ✅ Regroupe Description, Opt1-3 et Tags dans le champ "extra"
- ✅ **Filtre automatiquement les entrées invalides** (sans URL ni mot de passe)
- ✅ Génère un rapport des entrées ignorées dans un fichier `_ignores.txt`
- ✅ Affiche un aperçu des conversions réussies

### Syntaxe de base

```bash
python lockpass_to_passbolt.py <fichier_lockpass.csv> [fichier_sortie.csv]
```

### Exemples

1. **Conversion simple** (le fichier de sortie sera créé automatiquement) :
   ```bash
   python lockpass_to_passbolt.py lockpass_export.csv
   ```
   Cela créera un fichier `lockpass_export_passbolt.csv`

2. **Conversion avec nom de fichier personnalisé** :
   ```bash
   python lockpass_to_passbolt.py lockpass_export.csv mon_import_passbolt.csv
   ```

## 📊 Format des données

### Lockpass (Entrée)
Le script attend un CSV avec les colonnes suivantes (séparateur `;`) :
- Name
- Url
- Username
- Password
- Category/SubCategory
- Tags
- Description
- Opt1
- Opt2
- Opt3
- Totp
- Type

### Passbolt (Sortie)
Le script génère un CSV compatible LastPass avec les colonnes suivantes (séparateur `,`) :
- url
- username
- password
- extra (contient Description, Opt1, Opt2, Opt3 et Tags)
- name
- grouping (correspond à Category/SubCategory)
- fav (toujours 0 par défaut)
- totp

## 🔄 Correspondance des champs

| Lockpass | Passbolt | Note |
|----------|----------|------|
| Url | url | Copie directe |
| Username | username | Copie directe |
| Password | password | Copie directe |
| Name | name | Copie directe |
| Category/SubCategory | grouping | Copie directe |
| Totp | totp | Copie directe |
| Description | extra | Combiné avec Opt1-3 et Tags |
| Opt1 | extra | Ajouté dans le champ extra |
| Opt2 | extra | Ajouté dans le champ extra |
| Opt3 | extra | Ajouté dans le champ extra |
| Tags | extra | Ajouté dans le champ extra |
| - | fav | Toujours 0 (non favori) |

## 📥 Import dans Passbolt

1. Ouvrez Passbolt
2. Allez dans les paramètres d'import
3. Sélectionnez **"LastPass"** comme format d'import
4. Sélectionnez le fichier CSV généré par ce script
5. Suivez les instructions d'import de Passbolt

## ⚠️ Notes importantes

- Le script préserve toutes les informations de Lockpass dans le champ `extra` de Passbolt
- Les catégories et sous-catégories sont conservées dans le champ `grouping`
- Par défaut, tous les mots de passe sont marqués comme non favoris (fav=0)
- Les codes TOTP sont préservés
- **Les entrées sans URL ET sans mot de passe sont automatiquement ignorées** car Passbolt ne peut pas les importer
- Un fichier `_ignores.txt` est créé pour lister les entrées ignorées que vous devrez créer manuellement

### Pourquoi certaines entrées sont ignorées ?

Passbolt requiert au minimum :
- Une URL **OU** un mot de passe

Les entrées qui n'ont ni l'un ni l'autre ne peuvent pas être importées. Le script les filtre automatiquement et vous en informe via :
1. Un message dans la console
2. Un fichier rapport `*_ignores.txt` détaillé

### URLs trop longues (>1024 caractères)

Passbolt limite les URLs à 1024 caractères maximum. Si votre fichier Lockpass contient des URLs plus longues (souvent des URLs de connexion complexes avec tokens) :
- L'URL complète est déplacée dans le champ "extra"
- Le champ URL reste vide
- Le mot de passe et les autres informations sont préservés

### Codes TOTP invalides

Les codes TOTP doivent être au format **base32** (exemple: `JBSWY3DPEHPK3PXP`).
- Si Lockpass contient des codes TOTP invalides (comme "0000", "123456", etc.), ils sont déplacés dans le champ "extra"
- Les codes TOTP valides sont préservés dans le champ TOTP
- Vous pourrez configurer manuellement les TOTP dans Passbolt si nécessaire

## 🐛 Dépannage

### Erreur "Ko::buildOrCloneEntity expects data to be an object"
Cette erreur a été corrigée. Elle était causée par des entrées sans URL ni mot de passe. Le script filtre maintenant automatiquement ces entrées.

### Erreur "The uris.0 should be 1024 character in length maximum"
Cette erreur est maintenant gérée automatiquement. Les URLs trop longues sont déplacées dans le champ "extra".

### Erreur "The secret_key is not valid" (TOTP)
Les codes TOTP invalides sont maintenant automatiquement détectés et déplacés dans le champ "extra". Seuls les codes au format base32 valide sont conservés dans le champ TOTP.

### Message "Imported with default content type"
C'est un avertissement de Passbolt, pas une erreur. Vos données ont été importées avec succès, mais Passbolt n'a pas pu déterminer automatiquement le type de ressource pour certaines entrées (ex: pas d'URL). Ces entrées sont quand même importées.

### Entrées partiellement importées
Si vous voyez "Partiellement importé", vérifiez :
1. Le fichier `*_ignores.txt` pour voir les entrées qui n'ont pas pu être converties
2. Ces entrées devront être créées manuellement dans Passbolt

### Erreur d'encodage
Le script détecte automatiquement l'encodage de votre fichier. Si vous rencontrez toujours des problèmes :
1. Ouvrez votre fichier CSV dans un éditeur de texte (Notepad++, VS Code, etc.)
2. Réenregistrez-le en UTF-8
3. Réessayez la conversion

### Séparateur incorrect
Le script attend un séparateur `;` pour Lockpass. Si votre export utilise un autre séparateur, vous devrez modifier le fichier ou réexporter depuis Lockpass.

### Problèmes d'import dans Passbolt
Si l'import échoue :
1. Vérifiez que vous avez sélectionné "LastPass" comme format d'import
2. Assurez-vous que votre version de Passbolt supporte l'import LastPass
3. Vérifiez les logs d'erreur de Passbolt pour plus de détails

## 📝 Exemple de conversion

**Lockpass (entrée)** :
```
Name;Url;Username;Password;Category/SubCategory;Tags;Description;Opt1;Opt2;Opt3;Totp;Type
Compte Nas;192.168.0.1;sauvegarde;azerty123*;"Entreprise/NAS";nas sauvegarde;Mot de passe NAS;671282;1282;;cmzkplfkmdm6qzff
```

**Passbolt (sortie)** :
```
"url","username","password","extra","name","grouping","fav","totp"
"192.168.0.1","sauvegarde","azerty123*","Description: Mot de passe NAS | Opt1: 671282 | Opt2: 1282 | Tags: nas sauvegarde","Compte Nas","Entreprise/NAS","0","cmzkplfkmdm6qzff"
```

**Note** : Le champ "extra" utilise " | " comme séparateur pour une meilleure compatibilité avec Passbolt.

## 📄 Licence

Script créé pour faciliter la migration de Lockpass vers Passbolt.
