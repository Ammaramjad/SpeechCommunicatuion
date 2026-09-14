# VELORA — public link (किसी को भी भेजो)

## Problem
`http://127.0.0.1:4173` **sirf aapke PC par** chalta hai — share mat karo.

`velora-private-rides.surge.sh` tab tak **project not found** dikhayega jab tak Surge par login + deploy na ho.

---

## ✅ Recommended — GitHub Pages (free, permanent)

Code already `gh-pages` branch par hai. **Ek baar** ye enable karo:

1. Open: https://github.com/Ammaramjad/SpeechCommunicatuion/settings/pages  
2. **Build and deployment → Source:** `Deploy from a branch`  
3. **Branch:** `gh-pages` → folder `/ (root)` → **Save**  
4. 1–2 minute wait, phir open:

### **https://ammaramjad.github.io/SpeechCommunicatuion/**

Ye link phone, laptop, kisi ke bhi browser me chalega.

---

## Optional — Surge (Fleet OS style domain)

```bash
cd velora
npx surge login          # ek baar email/password
./deploy-surge.sh
```

Phir: **https://velora-private-rides.surge.sh/**

GitHub Action auto-deploy ke liye repo Settings → Secrets → `SURGE_TOKEN` add karo (`surge tokens add --domain velora-private-rides.surge.sh`).

---

## Temporary — apne laptop se turant link

```bash
cd velora
./share.sh
```

Terminal me `*.loca.lt` URL aayega (jab tak script chale).
