# Code signing the Windows build

Unsigned `.exe` files trigger two different warnings:

1. **Antivirus false positives.** PyInstaller apps are often flagged because they share a launcher
   ("bootloader") that malware also uses. Our build compiles its own bootloader from source and
   embeds proper version info, which clears most of these. If a specific antivirus still flags it,
   submit the file as a false positive (Microsoft Defender:
   https://www.microsoft.com/en-us/wdsi/filesubmission).
2. **SmartScreen ("Windows protected your PC").** Only a code-signing certificate, plus download
   reputation building up over time, makes this go away.

The build workflow is already wired for **Azure Artifact Signing** (Microsoft's managed signing
service, formerly "Trusted Signing"). It's available to individual developers in the US and
Canada, and the Basic plan is about $9.99/month. Signing switches on automatically as soon as the
secrets below exist; nothing in the code needs to change.

## One-time setup (about 30 minutes of your time, plus identity verification)

1. **Azure account.** Create one at https://azure.microsoft.com (it needs a credit card) and a
   pay-as-you-go subscription. Check that the billing account type is **Individual** and that your
   legal name and address are correct, because they go on the certificate.
2. **Artifact Signing account.** In the Azure portal, search "Artifact Signing Accounts" →
   Create. Pick a region (e.g. East US, endpoint `https://eus.codesigning.azure.net/`), a name
   (e.g. `sardinessigning`) and the **Basic** plan.
3. **Identity validation.** In that account → Identity validations → New → **Public** →
   Individual. You'll verify with a driver's licence or passport through Microsoft Authenticator.
   Approval can take a few hours to a few days.
4. **Certificate profile.** Certificate profiles → Add → type **Public Trust**, pick your
   approved identity, and name it (e.g. `sardines-public`).
5. **A login for GitHub.** Microsoft Entra ID → App registrations → New registration
   (e.g. `sardines-github-signer`). Note its *Application (client) ID* and *Directory (tenant) ID*.
   Under Certificates & secrets → New client secret, then copy the **value**.
6. **Permission.** In your Artifact Signing account → Access control (IAM) → Add role assignment
   → **Artifact Signing Certificate Profile Signer** → assign it to the app registration from step 5.
7. **GitHub secrets.** In the repo → Settings → Secrets and variables → Actions → New
   repository secret, add:

   | Secret | Value |
   |---|---|
   | `AZURE_TENANT_ID` | Directory (tenant) ID from step 5 |
   | `AZURE_CLIENT_ID` | Application (client) ID from step 5 |
   | `AZURE_CLIENT_SECRET` | Client secret value from step 5 |
   | `AZURE_SIGNING_ENDPOINT` | Your region's endpoint, e.g. `https://eus.codesigning.azure.net/` |
   | `AZURE_SIGNING_ACCOUNT` | Artifact Signing account name from step 2 |
   | `AZURE_SIGNING_PROFILE` | Certificate profile name from step 4 |

8. **Publish a signed release.** Actions → Test & Build → Run workflow → enter a version
   (e.g. `v0.2.0`). The Windows `.exe` is signed during the build.

## Free alternative for open-source projects

**SignPath Foundation** (https://signpath.org) signs open-source projects for free. It requires
an OSI-approved licence and a public repo, and the certificate names "SignPath Foundation" as the
publisher rather than you. It's an application process, not instant.
