# Evidence and identity trust boundary

- Evidence records require a submitter identity and retain verifier attribution after verification.
- The same caller-supplied identity cannot both submit and verify the same evidence record.
- Only configured verifier identifiers may verify evidence; only configured resolver identifiers may resolve dependencies.
- Only the designated decision owner may complete a ready case.
- Completed cases reject further mutations through the public methods.
- The evidence packet hash is a deterministic content hash for change detection. It is not a digital signature, hash chain, trusted timestamp or protection against direct database/code modification.
- Actor identifiers and authorization sets are supplied by the application caller. This prototype does not authenticate users or establish organizational identity.


## Constructor trust boundary

Initial case state may contain only unverified evidence records. Supplying an evidence record already marked verified is rejected during case construction; verification must pass through `verify_evidence()`, which checks the configured verifier allowlist and submitter/verifier separation. This remains an application-level control: the caller supplies actor identifiers and allowlists, so the prototype does not authenticate those identities.
