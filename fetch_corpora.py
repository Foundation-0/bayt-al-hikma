"""Pure-stdlib primary corpus fetcher & SHA-256 verifier for Foundation-0/bayt-al-hikma.

Downloads all 9 pinned primary Arabic and English corpora directly from their
upstream repositories/editions and verifies exact SHA-256 digests and byte sizes
before committing each file atomically into --dest.

Zero external dependencies. Zero floats. Zero bare assert statements.
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.request


USER_AGENT = "Foundation-0-bayt-al-hikma-fetch/1.0"

CORPUS_MANIFEST = (
    {
        "id": "leeds_morphology_v04",
        "rel_path": "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt",
        "url": (
            "https://raw.githubusercontent.com/cltk/arabic_morphology_quranic-corpus/"
            "b5abd4d8fadd775f3329f34cbe10531fac71e391/quranic-corpus-morphology-0.4.txt"
        ),
        "edition": "Quranic Arabic Corpus Morphology v0.4 (Kais Dukes, 2011; cltk mirror commit b5abd4d8)",
        "upstream_source": "https://corpus.quran.com/download / https://github.com/cltk/arabic_morphology_quranic-corpus",
        "licence": "GNU General Public License (GPL); verbatim unmodified redistribution required per file header",
        "expected_bytes": 6309503,
        "sha256": "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46",
    },
    {
        "id": "tanzil_quran_uthmani",
        "rel_path": "tanzil-quran-uthmani.txt",
        "url": "https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2",
        "edition": "Tanzil Quran Text (Uthmani, Version 1.1, pipe-delimited surah|ayah|text)",
        "upstream_source": "https://tanzil.net/download/",
        "licence": "Creative Commons Attribution 3.0 (CC-BY-3.0); verbatim unmodified text per file header",
        "expected_bytes": 1370878,
        "sha256": "bf4f57b968d03f4131c070b1e285da9be0e0a108a21c910e872801ca273312c8",
    },
    {
        "id": "tanzil_en_sahih",
        "rel_path": "tanzil-en.sahih.txt",
        "url": "https://tanzil.net/trans/en.sahih",
        "edition": "Saheeh International English Translation (Tanzil ID en.sahih, last update 2011-04-24)",
        "upstream_source": "https://tanzil.net/trans/",
        "licence": "Tanzil.net verbatim translation distribution (non-commercial / attribution per Tanzil terms)",
        "expected_bytes": 898049,
        "sha256": "a1778a1a56695d9b59ae910809ec46d9f4a55f05961de51cd56e6ebcf9040883",
    },
    {
        "id": "tanzil_en_pickthall",
        "rel_path": "tanzil-en.pickthall.txt",
        "url": "https://tanzil.net/trans/en.pickthall",
        "edition": "M. M. Pickthall English Translation (Tanzil ID en.pickthall, last update 2010-09-04)",
        "upstream_source": "https://tanzil.net/trans/",
        "licence": "Public Domain text / Tanzil.net verbatim distribution",
        "expected_bytes": 864918,
        "sha256": "4aabbfa9d96796f5a6b0217d2c39dce1a3084f772bf6f2650e37082a774e3cc7",
    },
    {
        "id": "openiti_ibn_muqaffa_kalila",
        "rel_path": "openiti_controls/ibn_muqaffa_kalila.txt",
        "url": (
            "https://raw.githubusercontent.com/OpenITI/0150AH/"
            "f9a52b5bbc3a65673fc73fb32331e7f33811c480/data/0139IbnMuqaffac/"
            "0139IbnMuqaffac.KalilaWaDimna/0139IbnMuqaffac.KalilaWaDimna.Shamela0026537-ara1"
        ),
        "edition": "OpenITI 0139IbnMuqaffac.KalilaWaDimna.Shamela0026537-ara1 (OpenITI/0150AH @ f9a52b5b)",
        "upstream_source": "https://github.com/OpenITI/0150AH / https://openiti.org/",
        "licence": "OpenITI research corpus (premodern public-domain text; OpenITI Zenodo releases CC-BY-NC-SA-4.0; GitHub repo carries no SPDX file)",
        "expected_bytes": 430145,
        "sha256": "0b55371e4c69f44ffb5a1876b11e174398f3f84f400302c24007bdf1004afdc9",
    },
    {
        "id": "openiti_ibn_muqaffa_adab_kabir",
        "rel_path": "openiti_controls/ibn_muqaffa_adab_kabir.txt",
        "url": (
            "https://raw.githubusercontent.com/OpenITI/0150AH/"
            "f9a52b5bbc3a65673fc73fb32331e7f33811c480/data/0139IbnMuqaffac/"
            "0139IbnMuqaffac.AdabKabir/0139IbnMuqaffac.AdabKabir.JK009203-ara1"
        ),
        "edition": "OpenITI 0139IbnMuqaffac.AdabKabir.JK009203-ara1 (OpenITI/0150AH @ f9a52b5b)",
        "upstream_source": "https://github.com/OpenITI/0150AH / https://openiti.org/",
        "licence": "OpenITI research corpus (premodern public-domain text; OpenITI Zenodo releases CC-BY-NC-SA-4.0; GitHub repo carries no SPDX file)",
        "expected_bytes": 95949,
        "sha256": "7b6aa0a311465a28ae5f52b04c919fd89118e8b29cb283ac96a71710c62381b1",
    },
    {
        "id": "openiti_imru_al_qays_diwan",
        "rel_path": "openiti_controls/imru_al_qays_diwan.txt",
        "url": (
            "https://raw.githubusercontent.com/OpenITI/0025AH/"
            "05bfb1cad632ff98d62c925c6a28c0e3b4e67a64/data/0001ImruQaysIbnHujr/"
            "0001ImruQaysIbnHujr.Diwan/0001ImruQaysIbnHujr.Diwan.JK007512-ara1"
        ),
        "edition": "OpenITI 0001ImruQaysIbnHujr.Diwan.JK007512-ara1 (OpenITI/0025AH @ 05bfb1ca)",
        "upstream_source": "https://github.com/OpenITI/0025AH / https://openiti.org/",
        "licence": "OpenITI research corpus (premodern public-domain text; OpenITI Zenodo releases CC-BY-NC-SA-4.0; GitHub repo carries no SPDX file)",
        "expected_bytes": 60731,
        "sha256": "7236a43a2309e92f556f6347d3b2279100eab606405563b2f07e9c54d1bd04d7",
    },
    {
        "id": "openiti_tarafa_diwan",
        "rel_path": "openiti_controls/tarafa_diwan.txt",
        "url": (
            "https://raw.githubusercontent.com/OpenITI/0025AH/"
            "05bfb1cad632ff98d62c925c6a28c0e3b4e67a64/data/0001TarafaIbnCabd/"
            "0001TarafaIbnCabd.Diwan/0001TarafaIbnCabd.Diwan.JK007518-ara2"
        ),
        "edition": "OpenITI 0001TarafaIbnCabd.Diwan.JK007518-ara2 (OpenITI/0025AH @ 05bfb1ca)",
        "upstream_source": "https://github.com/OpenITI/0025AH / https://openiti.org/",
        "licence": "OpenITI research corpus (premodern public-domain text; OpenITI Zenodo releases CC-BY-NC-SA-4.0; GitHub repo carries no SPDX file)",
        "expected_bytes": 47045,
        "sha256": "bde2655e74a09670c78decab34573e2913f2ba9e90b04438fc65410a49aedf38",
    },
    {
        "id": "openiti_antara_muallaqa",
        "rel_path": "openiti_controls/antara_muallaqa.txt",
        "url": (
            "https://raw.githubusercontent.com/OpenITI/0025AH/"
            "05bfb1cad632ff98d62c925c6a28c0e3b4e67a64/data/0001CantaraIbnShaddad/"
            "0001CantaraIbnShaddad.Mucallaqa/0001CantaraIbnShaddad.Mucallaqa.ShamAY0038527-ara1"
        ),
        "edition": "OpenITI 0001CantaraIbnShaddad.Mucallaqa.ShamAY0038527-ara1 (OpenITI/0025AH @ 05bfb1ca)",
        "upstream_source": "https://github.com/OpenITI/0025AH / https://openiti.org/",
        "licence": "OpenITI research corpus (premodern public-domain text; OpenITI Zenodo releases CC-BY-NC-SA-4.0; GitHub repo carries no SPDX file)",
        "expected_bytes": 7604,
        "sha256": "e346bde4145972d7ef243777cf6a02ced4ec96e0ddf402d5ad7f21b6d029eb38",
    },
)


class FetchError(ValueError):
    """Fail-closed corpus download or digest verification error."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _safe_dest_path(dest_dir, rel_path):
    if rel_path.startswith("/") or "\\" in rel_path or ".." in rel_path:
        raise FetchError("UNSAFE_REL_PATH", f"unsafe relative path {rel_path}")
    dest_real = os.path.realpath(dest_dir)
    full = os.path.realpath(os.path.join(dest_real, rel_path))
    if not full.startswith(dest_real + os.sep):
        raise FetchError("PATH_ESCAPE", f"resolved path escapes destination: {rel_path}")
    return full


def verify_directory(dest_dir):
    """Verify all 9 pinned corpora already exist in dest_dir with exact SHA-256 and size."""
    results = []
    for item in CORPUS_MANIFEST:
        full_path = _safe_dest_path(dest_dir, item["rel_path"])
        if not os.path.isfile(full_path):
            raise FetchError("CORPUS_MISSING", f"missing {item['rel_path']}")
        actual_size = os.path.getsize(full_path)
        actual_sha = sha256_file(full_path)
        if actual_size != item["expected_bytes"]:
            raise FetchError(
                "SIZE_MISMATCH",
                f"{item['rel_path']} size {actual_size} != {item['expected_bytes']}",
            )
        if actual_sha != item["sha256"]:
            raise FetchError(
                "SHA256_MISMATCH",
                f"{item['rel_path']} sha256 {actual_sha} != {item['sha256']}",
            )
        results.append({
            "id": item["id"],
            "rel_path": item["rel_path"],
            "status": "verified_existing",
            "bytes": actual_size,
            "sha256": actual_sha,
        })
    return {"dest_dir": os.path.basename(os.path.abspath(dest_dir)), "count": len(results), "files": results}


def fetch_all(dest_dir, timeout=30, force=False, opener=None):
    """Download missing (or all if force=True) corpora and verify SHA-256 atomically."""
    os.makedirs(dest_dir, exist_ok=True)
    fetch_fn = urllib.request.urlopen if opener is None else opener
    results = []
    for item in CORPUS_MANIFEST:
        full_path = _safe_dest_path(dest_dir, item["rel_path"])
        if not force and os.path.isfile(full_path):
            if os.path.getsize(full_path) == item["expected_bytes"] and sha256_file(full_path) == item["sha256"]:
                results.append({
                    "id": item["id"],
                    "rel_path": item["rel_path"],
                    "status": "cached_verified",
                    "bytes": item["expected_bytes"],
                    "sha256": item["sha256"],
                })
                continue
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        req = urllib.request.Request(item["url"], headers={"User-Agent": USER_AGENT})
        with fetch_fn(req, timeout=timeout) as resp:
            data = resp.read()
        actual_sha = sha256_bytes(data)
        if len(data) != item["expected_bytes"]:
            raise FetchError(
                "SIZE_MISMATCH",
                f"{item['id']} downloaded {len(data)} bytes != {item['expected_bytes']}",
            )
        if actual_sha != item["sha256"]:
            raise FetchError(
                "SHA256_MISMATCH",
                f"{item['id']} sha256 {actual_sha} != {item['sha256']}",
            )
        fd, tmp_path = tempfile.mkstemp(prefix=".fetch_", dir=os.path.dirname(full_path))
        try:
            with os.fdopen(fd, "wb") as tmp_f:
                tmp_f.write(data)
            os.replace(tmp_path, full_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        results.append({
            "id": item["id"],
            "rel_path": item["rel_path"],
            "status": "downloaded_verified",
            "bytes": len(data),
            "sha256": actual_sha,
        })
    return {"dest_dir": os.path.basename(os.path.abspath(dest_dir)), "count": len(results), "files": results}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Download and SHA-256-verify all 9 primary Arabic/English corpora."
    )
    parser.add_argument(
        "--dest",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpora"),
        help="Destination directory for downloaded corpora (default: ./corpora)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing files in --dest without network access",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if already present and verified",
    )
    parser.add_argument(
        "--manifest-json",
        action="store_true",
        help="Print the full pinned corpus manifest (URLs, editions, licences, SHA-256s) as JSON",
    )
    args = parser.parse_args(argv)

    if args.manifest_json:
        payload = {"count": len(CORPUS_MANIFEST), "corpora": list(CORPUS_MANIFEST)}
        sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
        return 0
    if args.verify_only:
        summary = verify_directory(args.dest)
    else:
        summary = fetch_all(args.dest, force=args.force)
    sys.stdout.write(json.dumps(summary, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
