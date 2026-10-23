"""Build the personal CS2 release from the verified source tag."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


TAG = "Z1ncV1-C"
COMMIT = "07fc257be6d59e6420f8e382709a0d64a159e714"
UPSTREAM = "e902881236a423fe44e48d01b02278149f645890"
FILES = (
    "auto.cfg",
    "crosshair.cfg",
    "crosshair_throw.cfg",
    "demo.cfg",
    "ffmpeg.cfg",
    "hlae.cfg",
    "practice.cfg",
    "pt.cfg",
    "pwapt.cfg",
    "solo.cfg",
    "ze.cfg",
    "README.md",
    "LICENSE",
    "使用说明.html",
    "启动项.txt",
)

NOTES = """合入 Purple-CSGO/CS2-Config-Presets 上游 v2.6e，保留 Ryuz1nc 个人设置，并完成个人准星字段迁移。

## 更新内容

- `auto.cfg`：同步兼容更新、网络说明与新增指令，保留个人参数、按键和别名。
- `demo.cfg` / `hlae.cfg`：更新 Demo 预测、TrueView、曝光、天空贴图与自定义持枪视角功能。
- `ffmpeg.cfg`：新增 ProRes LT、ProRes Proxy 和对应拉伸预设，保留原有默认录制配置。
- `practice.cfg`：新增上游文件名兼容入口，加载个人 `pt.cfg` 跑图设置。
- `pt.cfg` / `solo.cfg`：更新版本信息，保留原有功能和参数。
- 更新启动项说明及下载链接，不自动修改 Steam 启动项。

## 个人准星

保留绿色静态准星：大小 `0.8`、间距 `-3`、粗细 `0`、透明度 `200`、RGB `0 / 255 / 0`、样式 `4`、无描边。

补齐以下字段，值与已保存的个人设置一致：

```cfg
cl_crosshair_outlinethickness 0.5
cl_crosshair_recoil 0
cl_grenadecrosshair_keepusercrosshair 1
```

## 安装

下载 `Z1ncV1-C.zip`，备份现有配置后，将包内根目录的 11 个 `.cfg` 文件复制到游戏目录 `game\\csgo\\cfg`。
进入游戏后执行 `exec auto.cfg`；只加载准星时执行 `exec crosshair.cfg`。

本包包含 Ryuz1nc 的个人灵敏度、按键、准星、视角、ZE 和完美平台配置，其他玩家安装前请按个人习惯调整。
安装保留 `autoexec.cfg` 和 Steam 用户 VCFG。详细说明见包内 `INSTALL.md`。

## 校验

发布包提供 `manifest.json`、`SHA256SUMS.txt` 及单独的 ZIP 校验文件。
已完成静态检查和文件校验，未启动 CS2 或 HLAE 进行运行验证。

- 源码提交：`07fc257be6d59e6420f8e382709a0d64a159e714`
- 上游提交：`e902881236a423fe44e48d01b02278149f645890`

完整变更：https://github.com/Ryuz1nc/Ryuz1nc-s-CS2-Config-Presets/compare/Z1ncV1-B...Z1ncV1-C
"""

INSTALL = """# Z1ncV1-C 安装说明

1. 备份游戏目录 `game\\csgo\\cfg` 中现有的同名 CFG 文件。
2. 将本包根目录的 11 个 `.cfg` 文件复制到该目录。
3. 进入游戏后，在控制台执行 `exec auto.cfg`；只加载准星时执行 `exec crosshair.cfg`。
4. Steam 启动项沿用个人现有设置，本包不会自动更改启动项。

配置包含 Ryuz1nc 的灵敏度、按键、准星、持枪视角、ZE 和完美平台偏好。
其他玩家安装前应按个人习惯调整。`practice.cfg` 是兼容入口，执行 `exec pt.cfg`。

包内不含 `autoexec.cfg` 或 Steam 用户 VCFG；安装时保留这些现有文件。
Markdown、HTML、TXT 和 JSON 文件用于说明和校验，无需复制到游戏目录。

`SHA256SUMS.txt` 记录包内文件的 SHA-256。
发布页的 `.zip.sha256` 记录整个发布包的 SHA-256，可用 PowerShell 检查：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\\Z1ncV1-C.zip'
```

源码提交：`07fc257be6d59e6420f8e382709a0d64a159e714`。
发布前已做静态检查和文件校验，未启动 CS2 或 HLAE 进行运行验证。
"""


def git(*args):
    return subprocess.run(
        ["git", *args], check=True, stdout=subprocess.PIPE
    ).stdout


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    actual_commit = git("rev-parse", f"{TAG}^{{commit}}").decode().strip()
    if actual_commit != COMMIT:
        raise RuntimeError("Release tag does not point to the verified commit.")

    files = {name: git("show", f"{COMMIT}:{name}") for name in FILES}
    files["INSTALL.md"] = INSTALL.encode("utf-8")
    files["RELEASE-NOTES.md"] = NOTES.encode("utf-8")

    cfg_files = {name: data for name, data in files.items() if name.endswith(".cfg")}
    if len(cfg_files) != 11:
        raise RuntimeError("Release must contain exactly 11 CFG files.")
    for name, data in cfg_files.items():
        if any(line.startswith((b"<<<<<<< ", b">>>>>>> ")) for line in data.splitlines()):
            raise RuntimeError(f"Unresolved merge marker in {name}.")

    manifest = {
        "tag": TAG,
        "commit": COMMIT,
        "upstream_commit": UPSTREAM,
        "upstream_version": "v2.6e",
        "cfg_count": len(cfg_files),
        "files": [
            {"path": name, "size": len(data), "sha256": sha256(data)}
            for name, data in sorted(files.items())
        ],
    }
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    files["SHA256SUMS.txt"] = "".join(
        f"{sha256(data)}  {name}\n" for name, data in sorted(files.items())
    ).encode("utf-8")

    args.output.mkdir(parents=True, exist_ok=True)
    zip_path = args.output / f"{TAG}.zip"
    if zip_path.exists():
        raise FileExistsError(zip_path)
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = ZipInfo(name, date_time=(2026, 10, 23, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    with ZipFile(zip_path) as archive:
        if set(archive.namelist()) != set(files):
            raise RuntimeError("Archive file list mismatch.")
        for name, expected_data in files.items():
            if archive.read(name) != expected_data:
                raise RuntimeError(f"Archive data mismatch: {name}")

    digest = sha256(zip_path.read_bytes())
    zip_path.with_suffix(".zip.sha256").write_text(
        f"{digest}  {zip_path.name}\n", encoding="utf-8", newline="\n"
    )
    (args.output / "RELEASE.md").write_text(
        NOTES + f"\nZIP SHA-256：`{digest}`\n", encoding="utf-8", newline="\n"
    )
    print(f"Built {zip_path.name}: {len(files)} files, {len(cfg_files)} CFG files")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
