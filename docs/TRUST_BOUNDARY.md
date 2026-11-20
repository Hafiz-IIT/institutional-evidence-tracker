# Evidence and identity trust boundary

- Evidence records require a submitter identity and retain verifier attribution after verification.
- The same caller-supplied identity cannot both submit and verify the same evidence record.
- Only configured verifier identifiers may verify evidence; only configured resolver identifiers may resolve dependencies.
- Only the designated decision owner may complete a ready case.
- Completed cases reject further mutations through the public methods.
- The evidence packet hash is a deterministic content hash for change detection. It is not a digital signature, hash chain, trusted timestamp or protection against direct database/code modification.
- Actor identifiers and authorization sets are supplied by the application caller. This prototype does not authenticate users or establish organizational identity.
