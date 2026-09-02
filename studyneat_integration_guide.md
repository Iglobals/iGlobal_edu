# Studyneat API Integration Specification

This document details how to integrate your platform with Studyneat using our Single Sign-On (SSO) API. 

## Integration Overview

When a student purchases a textbook on your platform and clicks the "Access AI Features" button, the integration follows a secure two-step handshake:
1. **Server-to-Server Token Handshake**: Your backend makes a secure POST request to Studyneat to initialize a session and obtain a short-lived redirection link.
2. **User Redirection**: Your backend redirects the student's browser to the returned Studyneat link. Studyneat will automatically log the user in (or create an account if they are new) and load their purchased book.

```
+-------------+                    +-------------------+                    +-------------------+
|   Student   |                    |   Partner Server  |                    | Studyneat Backend |
|   Browser   |                    |                   |                    |                   |
+------+------+                    +---------+---------+                    +---------+---------+
       |   Access AI Features                |                                        |
       +------------------------------------>|                                        |
       |                                     |  POST /sso/session (w/ Client Keys)   |
       |                                     +--------------------------------------->|
       |                                     |                                        |
       |                                     |<---------------------------------------+
       |                                     |  Returns redirectUrl?token=xyz         |
       |  Redirect Browser to redirectUrl    |                                        |
       |<------------------------------------+                                        |
       |                                                                              |
       |  Loads Studyneat with book pre-loaded                                        |
       +----------------------------------------------------------------------------->|
```

---

## 1. Credentials
Before beginning, the Studyneat team will provide you with two keys for your environment:
* `x-client-key`: Your public partner ID.
* `x-client-secret`: Your private security key (this must be kept secure on your servers and **never** exposed in client-side code).

---

## 2. Step 1: Initialize Session (Backend API Call)

Make a server-to-server HTTP request from your server. Do not call this from the browser to avoid leaking your `x-client-secret`.

* **Method**: `POST`
* **Production Endpoint**: `https://studyneat-backend.onrender.com/api/partner/sso/session`
* **Staging/Local Endpoint**: `http://localhost:8000/api/partner/sso/session`

### Headers
| Header | Value | Description |
| :--- | :--- | :--- |
| `Content-Type` | `application/json` | Required |
| `x-client-key` | `YOUR_CLIENT_KEY` | Provided by Studyneat |
| `x-client-secret` | `YOUR_CLIENT_SECRET` | Provided by Studyneat |

### Request Body (JSON)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `email` | `String` | **Yes** | The student's email address (lowercase). |
| `name` | `String` | **Yes** | The student's full name. |
| `bookId` | `String` | **Yes** | The unique ID of the textbook. |

#### Example Request:
```json
{
  "email": "student@partner.com",
  "name": "Jane Doe",
  "bookId": "sen-201-software-engineering"
}
```

### Response
A successful handshake returns a `200 OK` with a temporary, single-use `redirectUrl` (valid for 5 minutes).

#### Example Response:
```json
{
  "success": true,
  "redirectUrl": "https://www.studyneat.xyz/sso/login?token=92e3a1f87ab29..."
}
```

---

## 3. Step 2: Redirect the Student's Browser

Once your backend receives the `redirectUrl` from the API, redirect the student’s browser to that URL. 

Example (Node.js/Express):
```javascript
res.redirect(response.data.redirectUrl);
```

On landing, Studyneat will:
1. Validate the single-use token.
2. Authenticate the student (auto-registering them if it is their first time).
3. Clone the textbook specified by the `bookId` into the student's personal documents.
4. Route them directly into the document workspace where they can immediately chat, generate flashcards, and take quizzes on the book.

---

## 4. Book Catalog Mapping

Please use the following Studyneat `bookId` codes when calling the API:

| Book Title | Studyneat `bookId` |
| :--- | :--- |
| **SEN 201: Introduction to Software Engineering** | `sen-201-software-engineering` |
| **JUPEB Biology Study Guide** | `jupeb-biology-test` |

*(If you need more textbooks added to the catalog, please provide the PDFs to the Studyneat admin team to pre-process them and obtain new `bookId` keys).*