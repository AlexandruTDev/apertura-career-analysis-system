{ pkgs ? import <nixpkgs> {} }:

let
  # Create a custom font configuration that points directly to used font package
  fontsConf = pkgs.makeFontsConf {
    fontDirectories = [ pkgs.dejavu_fonts ];
  };
in
pkgs.mkShell {
  buildInputs = [
    # --- System-level dependencies ---
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.chromium
    pkgs.chromedriver
    pkgs.fontconfig

    # --- Dependencies for weasyprint ---
    pkgs.pango
    pkgs.cairo
    pkgs.gdk-pixbuf

    # --- Python Packages from Nixpkgs ---
    (pkgs.python311.withPackages (ps: [
      ps.pandas
      ps.numpy
      ps.requests
      ps.beautifulsoup4
      ps.tqdm
      ps.streamlit
      ps.matplotlib
      ps.selenium
      ps.weasyprint
    ]))
  ];

  # 1. Set the environment variable so soccerdata can find our config.
  # 2. Install soccerdata and the correct version of 'packaging'.
  shellHook = ''
    # Tell the environment to use custom font configuration
    export FONTCONFIG_FILE="${fontsConf}"
    export SOCCERDATA_DIR="$HOME/soccerdata"
    
    python -m venv .venv
    source .venv/bin/activate
    pip install soccerdata "packaging<24"
  '';
}