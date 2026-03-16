# Gateway, Cross-Language Communication, P2P

**1. Evolutionary Egress Gateway Design**

- **Concept**: Abstract a `Network Gateway` layer within `AegisDispatcher` to shield upper-layer Agents from low-level network addressing details. When a recipient URI contains a non-local `instance_id`, gateway routing is automatically triggered.

    Phase 1: Personal Device Cluster ("Private Cloud" Mode —— Recommended for Early MVP)
    
    - **Underlying Technology**: **Tailscale / WireGuard (Virtual LAN)**
    - **How to Route**: You don't need to write complex P2P logic. Users install Tailscale on their phones, Macs, and cloud servers. Tailscale assigns a fixed virtual IP to each device (e.g., `100.x.x.x`).
    - **AegisOS Design**:
        - `instance_id` directly uses the virtual IP or Tailscale machine name (e.g., `planner@macbook-pro.local`).
        - The dispatcher connects directly to this virtual IP via standard TCP Sockets or gRPC.
    - **Pros**: Minimal code, invincible security (native end-to-end encryption, hackers cannot access your virtual network).
    - **Cons**: Not suitable for strangers (e.g., your Agent bargaining with another company's Agent); limited to your own devices.
    
    Phase 2: Federated Relay Bus ("Nostr / Matrix" Mode —— Recommended for Commercialization)
    
    - **Underlying Technology**: **WebSocket + Pub/Sub Relay**
    - **How to Route**: Instead of extreme pure P2P, we deploy several open-source relay servers (Relays, e.g., `wss://relay.aegisos.com`), similar to the Nostr protocol.
    - **AegisOS Design**:
        - All online Aegis instances connect to a Relay via WebSocket.
        - `instance_id` is a public key string.
        - When an Agent in Beijing wants to message an Agent in Singapore, it **encrypts** the message with the recipient's public key and sends it to the Relay: "Broadcast this to the instance with this public key." The Singapore instance decrypts it with its private key.
    - **Pros**: Perfectly solves NAT traversal; seamless collaboration across companies and firewalls. Since data is encrypted, the relay has no knowledge of the content.
    
    Phase 3: Pure Web3-Grade P2P ("IPFS / Libp2p" Mode —— Ultimate Vision)
    
    - **Underlying Technology**: [**Libp2p**](https://libp2p.io/) (the underlying network protocol for Ethereum and IPFS, with a mature Python library `py-libp2p`).
    - **How to Route**: Fully adopt DHT algorithms and WebRTC hole punching.
    - **AegisOS Design**:
        - Introduce a full P2P network stack. Each AegisOS instance joins the global Aegis network as a P2P node.
        - `send_to_remote` in the dispatcher calls `libp2p.send(peer_id, message)`.
    - **Pros**: The purest decentralized Agent OS, censorship-resistant, never paralyzed by official server downtime.
    - **Cons**: Extremely high system complexity and resource consumption; challenging for the Python environment.

To ensure our current code doesn't need a total rewrite later, our design should **shield upper-layer logic from low-level network details**.

Regardless of which solution is used in the future, in Phases 1 and 2, we only need an abstract **"Egress Gateway"** in `AegisDispatcher`:

```python
# dispatcher.py pseudo-code

async def send_to_remote(receiver_uri: str, message: AACPMessage):
    # Parse URI: {role}_{uuid}@{instance_id}
    _, instance_id = receiver_uri.split("@")
    
    # Reserve a configuration interface for seamless switching of network engines
    if CONFIG.network_mode == "tailscale":
        await send_via_grpc(instance_id, message)
    elif CONFIG.network_mode == "nostr_relay":
        await send_via_websocket(instance_id, message)
    elif CONFIG.network_mode == "libp2p":
        await send_via_dht(instance_id, message)
```

- **Update Goal**: Supplement the core components module in `architecture.md`.

**2. Hybrid Architecture: AI Logic + Low-level P2P Network (Python + Go Sidecar)**

- **Concept**: Give up on handling high-concurrency P2P state machines in Python. Adopt a "Sidecar Pattern": the main process (Python) focuses on AI logic, Agent dispatching, and sandbox control; an independent daemon (implemented in Go based on `go-libp2p`) focuses on Kademlia DHT addressing, NAT Hole Punching, and node keep-alive.
- **Update Goal**: Supplement `decisions.md` as a major decision.

**3. Cross-Language Communication (IPC via UDS/gRPC)**

- **Concept**: The Python main process and Go network daemon communicate via low-latency local Unix Domain Sockets (UDS) or localhost gRPC (Inter-Process Communication, IPC), rather than through the external network.
    
    **Architectural Flow:**
    
    1. **Python Side (AegisOS Main Process)**: Focuses on running AI, dispatching Agents, and executing sandboxes.
    2. **Go Side (AegisOS-Net Daemon)**: Responsible for one thing—maintaining the Libp2p network, DHT addressing, hole punching, and maintaining long-lived WebSocket connections.
    3. **Communication Bridge (IPC)**: The Python "Egress Gateway" communicates with the Go process on the same machine via local **Unix Domain Socket (UDS)** or **localhost gRPC**.
    
    **Code-level Logic:**
    
    ```python
    # Python Side: dispatcher.py
    async def send_to_remote_via_go(receiver_uri: str, message: AACPMessage):
        # Python ignores hole punching and DHT, just throws JSON to the local Go process
        async with grpc.aio.insecure_channel('unix:///tmp/aegisos_net.sock') as channel:
            stub = NetGatewayStub(channel)
            await stub.RouteMessage(receiver_uri, message.model_dump_json())
    ```
    

- **Update Goal**: Record in the addressing and collaboration mechanism of `architecture.md`.

**4. One-Click Installation via Pre-compiled Binary Bundling**

- **Concept**: To maintain a seamless installation experience (`uv add aegisos`), CI/CD will cross-compile the Go network engine into tiny executables for various platforms (Linux, macOS ARM, Windows) and bundle them directly into the Python `.whl` package (located in `src/aegisos/bin/`). Upon startup, the Python `Launcher` automatically identifies the OS and spawns the corresponding Go process in the background via `subprocess`.
    
    **Packaging and Deployment Pipeline:**
    
    1. **Automated Compilation via GitHub Actions**:
        When releasing a new version, the CI/CD pipeline uses Go to cross-compile the network layer code into independent executables for each platform:
        - `aegisos-net-linux-amd64`
        - `aegisos-net-darwin-arm64` (Mac M1/M2)
        - `aegisos-net-windows.exe`
    2. **Embed into Python Wheel Package**:
        During Python code packaging (building `.whl` files), these small binaries (typically 10-20MB) are placed directly in the `src/aegisos/bin/` directory.
    3. **Transparent User-side Startup (Managed via Subprocess)**:
        When a user runs `aegisos start`, the Python code detects the OS, finds the corresponding Go binary, and silently starts it in the background.
        
    **Startup Code Example:**
    
    ```python
    # src/aegisos/core/launcher.py
    import subprocess
    import sys
    import platform
    from pathlib import Path
    
    def start_go_network_daemon():
        # Locate the Go binary bundled in the pip package
        bin_dir = Path(__file__).parent.parent / "bin"
        
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            executable = bin_dir / "aegisos-net-darwin-arm64"
        elif platform.system() == "Windows":
            executable = bin_dir / "aegisos-net-windows.exe"
        # ... other platform checks
        
        # Spawn the Go network engine as a background sub-process
        # The lifecycle of the Go process is tied to the Python main process
        return subprocess.Popen([executable, "--socket", "/tmp/aegisos_net.sock"])
    ```

- **Update Goal**: Record in `decisions.md` (Deployment and Release Strategy) and `roadmap.md` Phase 4.
