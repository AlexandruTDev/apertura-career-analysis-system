{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.chromium
    pkgs.chromedriver
    (pkgs.python311.withPackages (ps: [
      ps.pandas
      ps.numpy
      ps.requests
      ps.beautifulsoup4
      ps.tqdm
      ps.streamlit
      ps.matplotlib
      ps.selenium
    ]))
  ];

  # --- THE FIX IS HERE ---
  # 1. Set the environment variable so soccerdata can find our config.
  # 2. Install soccerdata and the correct version of 'packaging'.
  shellHook = ''
    export SOCCERDATA_DIR="$HOME/soccerdata"
    
    python -m venv .venv
    source .venv/bin/activate
    pip install soccerdata "packaging<24"
  '';
}