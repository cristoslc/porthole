from __future__ import annotations

from dataclasses import dataclass, field

from porthole.config import DEFAULT_DOMAIN, DEFAULT_SUBNET


@dataclass
class Peer:
    name: str
    ip: str
    public_key: str
    private_key: str
    dns_name: str
    role: str  # hub, workstation, server, family
    reverse_ssh_port: int | None = None
    platform: str | None = None  # linux, macos, windows — controls Guacamole protocol

    def to_dict(self) -> dict:
        d: dict = {
            "name": self.name,
            "ip": self.ip,
            "public_key": self.public_key,
            "private_key": self.private_key,
            "dns_name": self.dns_name,
            "role": self.role,
        }
        if self.reverse_ssh_port is not None:
            d["reverse_ssh_port"] = self.reverse_ssh_port
        if self.platform is not None:
            d["platform"] = self.platform
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Peer:
        return cls(
            name=data["name"],
            ip=data["ip"],
            public_key=data["public_key"],
            private_key=data["private_key"],
            dns_name=data["dns_name"],
            role=data["role"],
            reverse_ssh_port=data.get("reverse_ssh_port"),
            platform=data.get("platform"),
        )


@dataclass
class HubConfig:
    endpoint: str  # e.g. hub.example.com:51820

    def to_dict(self) -> dict:
        return {"endpoint": self.endpoint}

    @classmethod
    def from_dict(cls, data: dict) -> HubConfig:
        return cls(endpoint=data["endpoint"])


@dataclass
class Network:
    hub: HubConfig
    peers: list[Peer] = field(default_factory=list)
    domain: str = DEFAULT_DOMAIN
    subnet: str = str(DEFAULT_SUBNET)
    guacamole_admin_password: str | None = None  # SOPS-encrypted at rest

    def to_dict(self) -> dict:
        d: dict = {
            "network": {
                "domain": self.domain,
                "subnet": self.subnet,
                "hub": self.hub.to_dict(),
                "peers": [p.to_dict() for p in self.peers],
            }
        }
        if self.guacamole_admin_password is not None:
            d["network"]["guacamole_admin_password"] = self.guacamole_admin_password
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Network:
        net = data["network"]
        return cls(
            domain=net.get("domain", DEFAULT_DOMAIN),
            subnet=net.get("subnet", str(DEFAULT_SUBNET)),
            hub=HubConfig.from_dict(net["hub"]),
            peers=[Peer.from_dict(p) for p in net.get("peers", [])],
            guacamole_admin_password=net.get("guacamole_admin_password"),
        )
