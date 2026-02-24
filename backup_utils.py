import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from database import exportar_snapshot_publico

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "auth",
    "saida",
    "backups",
}

EXCLUDED_FILES = {
    ".DS_Store",
    "Thumbs.db",
}


def _resolver_binario_rar():
    override = (os.environ.get("BACKUP_RAR_BINARY") or "").strip()
    if override:
        if os.path.isfile(override):
            return override
        located = shutil.which(override)
        if located:
            return located
        raise RuntimeError(f"BACKUP_RAR_BINARY invalido: {override}")

    for candidate in ("rar", "winrar"):
        located = shutil.which(candidate)
        if located:
            return located

    if os.name == "nt":
        windows_candidates = [
            r"C:\Program Files\WinRAR\Rar.exe",
            r"C:\Program Files\WinRAR\WinRAR.exe",
            r"C:\Program Files (x86)\WinRAR\Rar.exe",
            r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
        ]
        for candidate in windows_candidates:
            if os.path.isfile(candidate):
                return candidate

    return None


def _compactar_em_rar(arquivo_origem, arquivo_destino_rar, senha):
    rar_binary = _resolver_binario_rar()
    if not rar_binary:
        raise RuntimeError(
            "Binario RAR nao encontrado. Instale o rar/WinRAR no servidor "
            "ou configure BACKUP_RAR_BINARY com o caminho completo."
        )

    cmd = [
        rar_binary,
        "a",
        "-y",
        "-idq",
        "-ep1",
        "-ma5",
        "-m5",
        f"-hp{senha}",
        str(arquivo_destino_rar),
        str(arquivo_origem),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0 or not os.path.exists(arquivo_destino_rar):
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detalhe = stderr or stdout or f"codigo={result.returncode}"
        raise RuntimeError(f"Falha ao gerar RAR protegido: {detalhe}")


def _iter_project_files(project_root):
    root = Path(project_root).resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(root)
        rel_parts = set(rel.parts)
        if rel_parts & EXCLUDED_DIRS:
            continue

        if path.name in EXCLUDED_FILES:
            continue

        yield path, rel


def _write_database_snapshot_json(target_path):
    snapshot = exportar_snapshot_publico()
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)


def _build_plain_backup_tar(project_root, tar_output_path):
    with tempfile.TemporaryDirectory(prefix="trxbkp-db-") as tmp_dir:
        db_snapshot_path = Path(tmp_dir) / "database_snapshot.json"
        _write_database_snapshot_json(db_snapshot_path)

        with tarfile.open(tar_output_path, "w:gz") as tar:
            tar.add(db_snapshot_path, arcname="database_snapshot.json")
            for abs_path, rel_path in _iter_project_files(project_root):
                tar.add(abs_path, arcname=str(rel_path).replace("\\", "/"))


def criar_backup_criptografado(project_root, output_dir, password):
    if not password or not password.strip():
        raise ValueError("Senha de backup ausente.")

    root = Path(project_root).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_base_name = f"trxpro-backup-{stamp}"
    rar_path = out_dir / f"{backup_base_name}.rar"

    with tempfile.TemporaryDirectory(prefix="trxbkp-") as tmp_dir:
        tar_path = Path(tmp_dir) / f"{backup_base_name}.tar.gz"
        _build_plain_backup_tar(project_root=root, tar_output_path=tar_path)
        _compactar_em_rar(
            arquivo_origem=tar_path,
            arquivo_destino_rar=rar_path,
            senha=password.strip(),
        )

    try:
        os.chmod(rar_path, 0o600)
    except Exception:
        pass

    with open(rar_path, "rb") as f:
        rar_bytes = f.read()
    sha256_hash = hashlib.sha256(rar_bytes).hexdigest()

    return {
        "path": str(rar_path),
        "filename": rar_path.name,
        "size_bytes": rar_path.stat().st_size,
        "sha256": sha256_hash,
        "created_at_utc": stamp,
    }


def remover_backups_antigos(output_dir, keep_days=15):
    removed = []
    if keep_days <= 0:
        return removed

    out_dir = Path(output_dir)
    if not out_dir.exists():
        return removed

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)

    patterns = ("trxpro-backup-*.rar", "trxpro-backup-*.enc")
    for pattern in patterns:
        for file_path in out_dir.glob(pattern):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    file_path.unlink(missing_ok=True)
                    removed.append(str(file_path))
            except Exception:
                continue

    return removed
