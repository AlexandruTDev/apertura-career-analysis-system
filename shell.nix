# shell.nix (Updated for Progress Bars)
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.pandas
    pkgs.python311Packages.numpy
    pkgs.python311Packages.requests
    pkgs.python311Packages.beautifulsoup4
    
    # --- New package for the progress bar ---
    pkgs.python311Packages.tqdm
  ];
}