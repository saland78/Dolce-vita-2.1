# Manuale Tecnico: BakeryOS SaaS Platform

## 1. Architettura del Sistema

### Overview
BakeryOS è una piattaforma **SaaS (Software as a Service) Multi-Tenant** progettata per la gestione di pasticcerie artigianali.
Il sistema permette a molteplici pasticcerie di registrarsi, collegare il proprio e-commerce (WooCommerce) e gestire la produzione in totale isolamento dei dati.

### Stack Tecnologico
*   **Backend**: Python FastAPI (High Performance, Async).
*   **Database**: MongoDB (NoSQL) con driver Motor (Async).
*   **Frontend**: React.js 19 + TailwindCSS + Shadcn/UI.
*   **Sync Engine**: Servizio asincrono per la sincronizzazione bidirezionale con WooCommerce.

---

## 2. Sicurezza e Multi-Tenancy

### Isolamento dei Dati
Il sistema utilizza un approccio **Logical Separation** (Database condiviso, Collection condivise, ma dati filtrati via codice).
Ogni documento nel database (Ordine, Prodotto, Ingrediente) possiede un campo `bakery_id`.

### Autenticazione e Autorizzazione
1.  **Login**: OAuth2 via Google (Emergent Auth).
2.  **Sessioni**: Token UUIDv4 salvati in **HttpOnly Secure Cookies**.
3.  **Middleware**: Ogni richiesta API passa attraverso `get_current_user_and_bakery`, che:
    *   Verifica il cookie di sessione.
    *   Identifica l'utente.
    *   Recupera il `bakery_id` associato.
    *   **Inietta** il `bakery_id` nel contesto della richiesta.
4.  **Query Scoping**: Tutte le query al database includono forzatamente `{"bakery_id": context.bakery_id}`, impedendo a un utente di vedere i dati di un'altra pasticceria.

---

## 3. Moduli Funzionali

### A. Gestione Ordini
*   **Importazione**: Automatica da WooCommerce ogni 60 secondi.
*   **Stati**: Received -> In Production -> Ready -> Delivered.
*   **Logica Archiviazione**: Gli ordini completati possono essere archiviati per mantenere la dashboard pulita.

### B. Piano di Produzione
*   **Aggregazione**: Algoritmo che scansiona tutti gli ordini aperti e raggruppa gli articoli identici (es. 5 ordini da 2 cornetti = 10 cornetti totali).
*   **Persistenza**: Lo stato di completamento (check) è salvato nel DB per ogni data e pasticceria.

### C. Magazzino e Ricette (Next Step)
*   Struttura pronta per collegare Prodotti Finiti a Ingredienti Grezzi.

---

## 4. Specifiche API (Endpoint Principali)

| Metodo | Endpoint | Descrizione |
| :--- | :--- | :--- |
| `GET` | `/api/orders` | Lista ordini filtrata per Tenant. |
| `GET` | `/api/orders/production-plan` | Aggregato di produzione giornaliera. |
| `GET` | `/api/sales-history` | Statistiche vendite (Oggi, 7gg, Mese). |
| `POST` | `/api/auth/session` | Scambio token OAuth -> Sessione BakeryOS. |

---

## 5. Procedura di Deployment (Messa Online)

### Requisiti
*   **VPS**: Server Linux (Ubuntu 22.04) con almeno 2GB RAM.
*   **Dominio**: Un dominio registrato (es. `bakeryos.app`).
*   **Docker**: Docker Engine & Docker Compose installati.

### Sicurezza in Produzione
1.  **HTTPS**: Obbligatorio (gestito da Traefik o Nginx + Let's Encrypt).
2.  **Cookie**: Impostare `Secure=True` e `SameSite=Strict`.
3.  **CORS**: Limitare `Allow-Origins` solo al dominio del frontend.
4.  **Database**: MongoDB non deve mai essere esposto su internet (bind IP 127.0.0.1 o rete interna Docker).

---

**BakeryOS Technical Dept.**
*Generated automatically by Emergent Agent*
