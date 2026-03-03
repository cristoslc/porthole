"""Ansible lookup plugin: decrypt network.sops.yaml and return network state dict.

Usage in a playbook::

    vars:
      net_state: "{{ lookup('sops_state', '../network.sops.yaml') }}"
      net:        "{{ net_state.network }}"
      hub_peer:   "{{ net.peers | selectattr('role','equalto','hub') | first }}"
      spoke_peers:"{{ net.peers | rejectattr('role','equalto','hub') | list }}"

The plugin runs ``sops -d --output-type json <path>`` and returns the parsed
JSON dict.  SOPS must be on PATH and the age key must be available at the
standard location (``~/.config/sops/age/keys.txt``) or via ``SOPS_AGE_KEY_FILE``.
"""
from __future__ import annotations

import json
import subprocess

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):  # noqa: ANN001
        results = []
        for term in terms:
            path = self._loader.path_dwim(term)
            try:
                proc = subprocess.run(
                    ["sops", "-d", "--output-type", "json", path],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except FileNotFoundError as exc:
                raise AnsibleError("sops binary not found on PATH") from exc
            except subprocess.CalledProcessError as exc:
                raise AnsibleError(
                    f"sops failed to decrypt {path!r}: {exc.stderr.strip()}"
                ) from exc

            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                raise AnsibleError(
                    f"sops output for {path!r} is not valid JSON: {exc}"
                ) from exc

            results.append(data)

        return results
