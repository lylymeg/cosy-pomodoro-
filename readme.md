# 🌿 Cosy Focus Timer & To-Do Studio

Application de productivité développée en Python avec PyQt5, combinant la technique Pomodoro, un générateur de bruits d'ambiance synthétiques en continu et une To-Do list interactive.

---

## 🌟 Fonctionnalités

- **Gestionnaire Pomodoro** :
  - Modes : Session de travail (25m), Pause courte (5m), Pause longue (15m).
  - Suivi dynamique des Pomodoros complétés.
  - Barre de progression visuelle réactive.

- **🎧 Générateur Audio Synthétique** :
  - Flux audio généré en temps réel via `sounddevice` sans aucun fichier audio externe.
  - Options d'ambiance : **🌧️ Pluie**, **☕ Café**, **📻 Bruit Blanc**.

- **📝 To-Do List Intégrée** :
  - Ajout rapide de tâches.
  - Case à cocher avec style barré lors de la validation.
  - Suppression individuelle de tâches.

---

## 🛠️ Installation et Lancement

Installez les dépendances :

pip install PyQt5 sounddevice numpy scipy