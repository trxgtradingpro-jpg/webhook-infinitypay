from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

import backup_utils


def test_criar_backup_gera_rar_protegido(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    output_dir = tmp_path / "out"
    project_root.mkdir()
    output_dir.mkdir()

    def fake_build_plain_backup_tar(project_root, tar_output_path):
        Path(tar_output_path).write_bytes(b"dummy-tar-content")

    monkeypatch.setattr(backup_utils, "_build_plain_backup_tar", fake_build_plain_backup_tar)
    monkeypatch.setattr(backup_utils, "_resolver_binario_rar", lambda: "rar")

    recorded = {}

    def fake_run(cmd, capture_output, text, timeout, check):
        recorded["cmd"] = cmd
        rar_output = Path(cmd[-2])
        rar_output.write_bytes(b"dummy-rar-content")

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr(backup_utils.subprocess, "run", fake_run)

    info = backup_utils.criar_backup_criptografado(
        project_root=str(project_root),
        output_dir=str(output_dir),
        password="admin-123",
    )

    assert info["filename"].endswith(".rar")
    assert Path(info["path"]).exists()
    assert "-hpadmin-123" in recorded["cmd"]


def test_criar_backup_falha_sem_binario_rar(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    output_dir = tmp_path / "out"
    project_root.mkdir()
    output_dir.mkdir()

    def fake_build_plain_backup_tar(project_root, tar_output_path):
        Path(tar_output_path).write_bytes(b"dummy-tar-content")

    monkeypatch.setattr(backup_utils, "_build_plain_backup_tar", fake_build_plain_backup_tar)
    monkeypatch.setattr(backup_utils, "_resolver_binario_rar", lambda: None)

    with pytest.raises(RuntimeError, match="Binario RAR nao encontrado"):
        backup_utils.criar_backup_criptografado(
            project_root=str(project_root),
            output_dir=str(output_dir),
            password="admin-123",
        )
