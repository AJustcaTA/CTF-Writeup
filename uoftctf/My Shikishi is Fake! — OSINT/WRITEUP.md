## My Shikishi is Fake! — OSINT

Goal: Find a long-running “high-quality fake shikishi certificate” operation and build the flag:

`uoftctf{JPNAME_EMAIL_YEAR_CERT}`

The challenge asks for 4 items:

1. The appraiser’s **first and last name in Japanese** (exactly as shown on the certificate).
2. An **email address** tied to one of the organizations that issued the certificate.
3. The **year** they were “reborn” and started expanding their activities.
4. PSA authenticated one of these fakes (a Draken & Mikey / Ken Wakui-related shikishi). Find the **PSA certification number**.

---

## 1) Identify the fake certificate system + the constant appraiser name

### OSINT idea

The challenge says the organization names change over time, across sellers and platforms, but **the appraiser name stays the same**.
So the first priority is to find **certificate samples (COA templates)** shown in listings or posts and read the appraiser name directly from the certificate.

### What I did

I searched using Japanese/English keywords like:

* “shikishi certificate sample”
* “色紙 鑑定書 見本”
* “国際 美術 鑑定 研究所 色紙”

These searches lead to pages/images showing the “certificate sample” used with shikishi autographs. The same appraiser name appeared on these certificates:

✅ **大山弘之**

Important: The challenge requires the name **in Japanese exactly as written on the certificate**, so I copied it in that exact form.

---

## 2) Find the issuing organization’s email address

### OSINT idea

The prompt asks for an email “tied to one of the organizations the certificate is issued by.”
That means the email must belong to the **certificate/issuing organization**, not a community warning site or unrelated collector resource.

### What I did

From the organization name printed/claimed on the certificate (e.g., related “international art appraisal/authentication” style names), I followed the trail to the organization’s contact information and extracted the email.

✅ Email found: **[information@sony.main.jp](mailto:information@sony.main.jp)**

Common pitfall: It’s easy to accidentally use an email from an *exposure / warning / discussion* site (like ShikishiBase), but that is **not** the issuing organization of the certificate and will produce a wrong flag.

---

## 3) Determine the “reborn / expanded activities” year

### OSINT idea

This phrase usually refers to a specific change such as:

* New branding or a “restart”
* Expanding into more categories
* Introducing anti-counterfeit features like holograms / serial numbers

### What I did

I examined the fine print on certificate sample images and related descriptions. These often mention when certain “systems” started (e.g., hologram + serial implementation).

✅ Year identified: **2015**

This matches the point where the operation “restarted” or upgraded its process (commonly described as the expansion phase).

---

## 4) PSA “oopsie” — find the certification number for the authenticated fake

### OSINT idea

The prompt explicitly says a foreign collector bought one and posted it.
So the fastest route is social media OSINT (Instagram / Reddit / X), looking for a post that includes:

* PSA LOA (Letter of Authenticity)
* A PSA verification link
* A visible cert number

### What I did

I located an Instagram post by **vroryn_TCG** showing the PSA LOA / related documentation and a PSA verification page.

From the PSA verification result:

* Item: *Shikishi: SIGNER KEN WAKUI*
* Cert Number: **AN09181**

✅ PSA cert number: **AN09181**

---

## 5) Assemble the final flag

| Field  | Value                                                       |
| ------ | ----------------------------------------------------------- |
| JPNAME | 大山弘之                                                        |
| EMAIL  | [information@sony.main.jp](mailto:information@sony.main.jp) |
| YEAR   | 2015                                                        |
| CERT   | AN09181                                                     |

✅ **Final Flag:**
`uoftctf{大山弘之_information@sony.main.jp_2015_AN09181}`

---

## why earlier attempts fail

* **Using `shikishibase@gmail.com`**:
  ShikishiBase is an information/analysis site about shikishi fakes, but the challenge asks for an email tied to the **certificate issuing organization**. Therefore the correct email is `information@sony.main.jp`, not ShikishiBase’s contact email.

---

If you want, paste your screenshots into a doc and I can help you format this into a clean “CTF writeup” style with Evidence sections and citation captions.
