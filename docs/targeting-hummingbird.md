# Targeting Hummingbird

The factory's published RPMs use the `.hum1.rpmfactory` release suffix. Tine supplies the Fedora
46 buildroot used for package builds; Warbler and Woodpecker consume the resulting repository by
its pinned OCI digest. The publish gate checks the assembled repository before publication.
