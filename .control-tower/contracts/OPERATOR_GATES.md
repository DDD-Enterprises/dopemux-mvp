# Operator Gates

The generic baseline keeps these operator-only:

- merge;
- force push;
- history rewrite;
- branch protection changes;
- branch deletion;
- credential / permission changes;
- production mutation;
- migrations;
- publication / activation;
- explicit security residual-risk acceptance.

Project governance may require additional gates such as ready-state promotion or external audit export. Configure them in `.control-tower/project.json` and the active Task Packet.
