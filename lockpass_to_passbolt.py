#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertisseur Lockpass vers Passbolt (format LastPass)
Ce script convertit un fichier CSV exporté de Lockpass vers le format CSV compatible avec Passbolt
"""

import csv
import sys
import os
import codecs


def detect_encoding(file_path):
    """
    Détecte l'encodage d'un fichier en testant les encodages courants
    
    Args:
        file_path: Chemin vers le fichier
    
    Returns:
        L'encodage détecté ou None
    """
    # Liste des encodages à tester (dans l'ordre de priorité)
    encodings = [
        'utf-8-sig',  # UTF-8 avec BOM
        'utf-8',
        'utf-16',
        'utf-16-le',
        'utf-16-be',
        'latin-1',
        'cp1252',
        'iso-8859-1'
    ]
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Essayer de lire le fichier entier
                content = f.read()
                # Si on arrive ici, l'encodage fonctionne
                print(f"✓ Encodage détecté : {encoding}")
                return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            continue
    
    return None


def convert_lockpass_to_passbolt(input_file, output_file):
    """
    Convertit un fichier CSV Lockpass vers le format Passbolt (LastPass)
    
    Args:
        input_file: Chemin vers le fichier CSV Lockpass
        output_file: Chemin vers le fichier CSV de sortie pour Passbolt
    """
    
    # Vérifier que le fichier d'entrée existe
    if not os.path.exists(input_file):
        print(f"❌ Erreur : Le fichier '{input_file}' n'existe pas.")
        return False
    
    # Détecter l'encodage du fichier
    print("🔍 Détection de l'encodage du fichier...")
    encoding = detect_encoding(input_file)
    
    if encoding is None:
        print("❌ Erreur : Impossible de détecter l'encodage du fichier.")
        print("   Essayez de réexporter votre fichier depuis Lockpass en UTF-8.")
        return False
    
    try:
        # Lire le fichier Lockpass
        with open(input_file, 'r', encoding=encoding) as f_in:
            # Lockpass utilise ; comme séparateur
            # QUOTE_ALL pour gérer les champs avec des ; dans leur contenu
            reader = csv.DictReader(f_in, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Préparer les données pour Passbolt
            passbolt_data = []
            skipped_entries = []
            long_url_count = 0
            invalid_totp_count = 0
            
            for row in reader:
                # Construire le champ "extra" avec Description et les champs Opt
                # Utiliser " | " comme séparateur au lieu de sauts de ligne pour compatibilité Passbolt
                extra_parts = []
                
                if row.get('Description', '').strip():
                    extra_parts.append(f"Description: {row['Description'].strip()}")
                
                if row.get('Opt1', '').strip():
                    extra_parts.append(f"Opt1: {row['Opt1'].strip()}")
                
                if row.get('Opt2', '').strip():
                    extra_parts.append(f"Opt2: {row['Opt2'].strip()}")
                
                if row.get('Opt3', '').strip():
                    extra_parts.append(f"Opt3: {row['Opt3'].strip()}")
                
                if row.get('Tags', '').strip():
                    extra_parts.append(f"Tags: {row['Tags'].strip()}")
                
                # Utiliser " | " comme séparateur au lieu de \n
                extra = ' | '.join(extra_parts)
                
                # Récupérer et nettoyer les champs
                url = row.get('Url', '').strip()
                username = row.get('Username', '').strip()
                password = row.get('Password', '').strip()
                name = row.get('Name', '').strip()
                grouping = row.get('Category/SubCategory', '').strip()
                totp = row.get('Totp', '').strip()
                
                # Valider et nettoyer l'URL (max 1024 caractères pour Passbolt)
                if len(url) > 1024:
                    long_url_count += 1
                    # Déplacer l'URL trop longue dans le champ extra
                    if extra:
                        extra = f"URL complète: {url} | {extra}"
                    else:
                        extra = f"URL complète: {url}"
                    url = ""  # Vider l'URL pour éviter l'erreur
                
                # Valider le code TOTP (doit être en base32 valide ou vide)
                # Les codes TOTP invalides (comme "0000", "740094760", etc.) doivent être déplacés dans extra
                if totp:
                    # Un code TOTP valide est en base32: lettres A-Z et chiffres 2-7, minimum 16 caractères
                    import re
                    if not re.match(r'^[A-Z2-7]{16,}$', totp.upper()):
                        invalid_totp_count += 1
                        # Code TOTP invalide, le déplacer dans extra
                        if extra:
                            extra = f"Code TOTP original: {totp} | {extra}"
                        else:
                            extra = f"Code TOTP original: {totp}"
                        totp = ""  # Vider le TOTP invalide
                
                # Créer la ligne pour Passbolt (format LastPass)
                passbolt_row = {
                    'url': url,
                    'username': username,
                    'password': password,
                    'extra': extra,
                    'name': name,
                    'grouping': grouping,
                    'fav': '0',  # Par défaut non favori
                    'totp': totp
                }
                
                # Vérifier que l'entrée a au moins une URL ou un mot de passe
                # Passbolt ne peut pas importer des entrées sans ces informations
                if not passbolt_row['url'] and not passbolt_row['password']:
                    skipped_entries.append({
                        'name': passbolt_row['name'],
                        'username': passbolt_row['username'],
                        'reason': 'Pas d\'URL ni de mot de passe'
                    })
                    continue
                
                passbolt_data.append(passbolt_row)
        
        # Écrire le fichier Passbolt en UTF-8 avec BOM pour compatibilité Excel
        with open(output_file, 'w', encoding='utf-8-sig', newline='', errors='strict') as f_out:
            fieldnames = ['url', 'username', 'password', 'extra', 'name', 'grouping', 'fav', 'totp']
            # Utiliser QUOTE_ALL pour assurer la compatibilité avec Passbolt
            writer = csv.DictWriter(f_out, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            
            writer.writeheader()
            writer.writerows(passbolt_data)
        
        print(f"✅ Conversion réussie !")
        print(f"📁 Fichier d'entrée : {input_file}")
        print(f"📁 Fichier de sortie : {output_file} (encodage: UTF-8 avec BOM)")
        print(f"📊 {len(passbolt_data)} mot(s) de passe converti(s)")
        
        # Afficher les avertissements
        if long_url_count > 0:
            print(f"⚠️  {long_url_count} URL(s) trop longue(s) (>1024 car.) déplacée(s) dans le champ 'extra'")
        
        if invalid_totp_count > 0:
            print(f"⚠️  {invalid_totp_count} code(s) TOTP invalide(s) déplacé(s) dans le champ 'extra'")
            print(f"   ℹ️  Les codes TOTP doivent être en format base32 (ex: JBSWY3DPEHPK3PXP)")
        
        # Afficher et sauvegarder les entrées ignorées
        if skipped_entries:
            print(f"⚠️  {len(skipped_entries)} entrée(s) ignorée(s) (pas d'URL ni de mot de passe)")
            
            # Créer un fichier de rapport pour les entrées ignorées
            skipped_file = output_file.replace('.csv', '_ignores.txt')
            with open(skipped_file, 'w', encoding='utf-8') as f:
                f.write("Entrées ignorées lors de la conversion\n")
                f.write("=" * 60 + "\n\n")
                f.write("Ces entrées n'ont ni URL ni mot de passe et ne peuvent pas être importées dans Passbolt.\n")
                f.write("Vous devrez les créer manuellement si nécessaire.\n\n")
                
                for i, entry in enumerate(skipped_entries, 1):
                    f.write(f"{i}. {entry['name']}\n")
                    if entry['username']:
                        f.write(f"   Username: {entry['username']}\n")
                    f.write(f"   Raison: {entry['reason']}\n\n")
            
            print(f"📄 Rapport des entrées ignorées : {skipped_file}")
        
        # Afficher un aperçu des noms convertis
        print(f"\n📋 Aperçu des mots de passe convertis :")
        for i, data in enumerate(passbolt_data[:5], 1):  # Afficher max 5 entrées
            print(f"   {i}. {data['name']}")
        if len(passbolt_data) > 5:
            print(f"   ... et {len(passbolt_data) - 5} autre(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion : {str(e)}")
        return False


def main():
    """Fonction principale"""
    
    print("=" * 60)
    print("🔐 Convertisseur Lockpass → Passbolt")
    print("=" * 60)
    print()
    
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python {sys.argv[0]} <fichier_lockpass.csv> [fichier_sortie.csv]")
        print()
        print("Exemples:")
        print(f"  python {sys.argv[0]} lockpass_export.csv")
        print(f"  python {sys.argv[0]} lockpass_export.csv passbolt_import.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Si pas de fichier de sortie spécifié, créer un nom automatique
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_passbolt.csv"
    
    # Effectuer la conversion
    success = convert_lockpass_to_passbolt(input_file, output_file)
    
    if success:
        print()
        print("📌 Prochaines étapes :")
        print("   1. Ouvrez Passbolt")
        print("   2. Allez dans les paramètres d'import")
        print("   3. Sélectionnez 'LastPass' comme format")
        print(f"   4. Importez le fichier : {output_file}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()