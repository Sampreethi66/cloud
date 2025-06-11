[cloud](../../../)
# Firebase + Flask Auth Setup

By Revanth

This project contains a simple Flask app deployed using Firebase Hosting, with authentication handled by Firebase Authentication.

Supports:

- ✅ Email/password login
- ✅ GitHub OAuth login
- ✅ Passwordless sign-in via email link (for registered users only)

Provides a command-based deployment and portable structure.

---

## 🔧 Prerequisites
- Python 3.12 or higher
- Firebase CLI installed (https://firebase.google.com/docs/cli)
- A GitHub developer account
- A Firebase project (free Spark tier is sufficient)

---

## 📦 Project Setup

### 1. Clone the Cloud Repo
```bash
git clone https://github.com/matterevanth/cloud.git
cd cloud/team/2025/revanth
```

### 2. Set up Firebase Hosting (Command-Based)
```bash
firebase login
firebase init hosting
```
- Select: `Use an existing project`
- Choose your Firebase project
- Public directory: `templates`
- Configure as single-page app? → `No`
- Overwrite index.html? → `No`

This will generate `.firebaserc` and `firebase.json`.

### 3. Set up Authentication Providers (Command-Based via Console)
While enabling auth requires Firebase Console, here are the manual steps:

#### A. Email/Password and Email Link
1. Run:
```bash
firebase open hosting:site
```
2. Go to: `Authentication > Sign-in method`
3. Enable:
   - Email/Password
   - Email Link (passwordless)
     - Redirect URL: `https://your-firebase-hosting-domain/finishSignIn.html`

#### B. GitHub Authentication
1. Go to: https://github.com/settings/developers → OAuth Apps → New OAuth App
2. Application name: `ModelEarth Auth`
3. Homepage URL:
```bash
https://your-project-id.firebaseapp.com
```
4. Authorization callback URL:
```bash
https://your-project-id.firebaseapp.com/__/auth/handler
```
5. Copy client ID and client secret → Paste into Firebase Console GitHub Auth provider settings

### 4. Add Authorized Domains
In the Firebase Console under `Authentication > Settings`, add:
- `localhost`
- `your-project-id.firebaseapp.com`
- `your-project-id.web.app`

---

## 🔑 Firebase API Key Setup

### A. Create Firebase Web App
```bash
firebase open project
```
- Click on the `</>` Web icon under "Your apps"
- Register app → Copy config snippet:

```js
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "...",
  appId: "..."
};
```

### B. Replace Firebase Config in These Files
Update the Firebase config block inside:
- `templates/login.html`
- `templates/finishSignIn.html`
- (Optional) `templates/sendlink.html`

---

## 📂 Files Overview
```
Root Folder(Revanth)/
├── app.py                  # Flask app (serves templates)
├── app.yaml                # Firebase deployment config (not used directly)
├── firebase.json           # Firebase Hosting setup (rewrites for each HTML)
├── .firebaserc             # Firebase project mapping
├── requirements.txt        # Python dependencies
└── templates/
    ├── index.html
    ├── login.html
    ├── signup.html
    ├── success.html
    ├── failure.html
    ├── finishSignIn.html   # For email link redirection
    ├── sendlink.html       # (Optional - split version)
    └── 404.html
```

---

## 🚀 Deploy to Firebase Hosting (Command-Based)
From inside `team/2025/revanth/`:
```bash
firebase deploy
```

After deploy, your site will be live at:
```bash
https://your-project-id.web.app/
```

---

## 🧪 Test the App
1. Go to `/signup.html` → Register with email/password
2. Go to `/login.html` and test:
   - Email/password login
   - GitHub login
   - Email link login
3. After clicking the link in your email, you’ll be redirected to `finishSignIn.html` → then to `success.html`

---

## 📬 Contact
Created by Revanth Matte for the Cloud Team.

To contribute, fork and PR to the `ModelEarth/cloud` repository.


