{
  description = "Get links of Discovery shows and a specific season and/or episode";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils, ... }:

    let
      version =
        if (self ? shortRev)
        then self.shortRev
        else "dev";
    in

    utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [ pkgs.go ];
        };
        packages.default = pkgs.buildGoModule {
          pname = "get-dmax-links";
          inherit version;
          src = pkgs.lib.cleanSource self;

          # Update the hash if go dependencies change!
          # vendorHash = pkgs.lib.fakeHash;
          vendorHash = "sha256-HvWeMD3vfLGvFA5qdqkuPNCJwIweP60lvEkFgo98t44=";

          ldflags = [ "-s" "-w" ];

          nativeBuildInputs = [ pkgs.installShellFiles ];
          postInstall = ''
            installShellCompletion --cmd get-dmax-links \
              --bash <($out/bin/get-dmax-links --completion)
          '';

          meta = {
            description = "Get links of Discovery shows and a specific season and/or episode";
            homepage = "https://github.com/Brawl345/Get-DMAX-Links";
            license = pkgs.lib.licenses.mit;
            platforms = pkgs.lib.platforms.darwin ++ pkgs.lib.platforms.linux;
          };
        };
      });
}
