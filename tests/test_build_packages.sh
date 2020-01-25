#/usr/bin/env bash
base="alpine"
repo="None"
tag="None"
image="None"
mounts=()
umounts() {
    for i in "${mounts[@]}"; do
        umount $i
        echo $mounts
        mounts=("${mounts[@]/$i}")
        echo $mounts
    done
}
trap umounts 0
ctr=$(buildah from $base)
mnt=$(buildah mount $ctr)
mounts=("$mnt" "${mounts[@]}")
buildah run --user root $ctr -- mkdir -p /var/cache/apk
mkdir -p $(pwd)/.cache/apk
mount -o bind $(pwd)/.cache/apk $mnt/var/cache/apk
mounts=("$mnt/var/cache/apk" "${mounts[@]}")
buildah run $ctr -- ln -s /var/cache/apk /etc/apk/cache
old="$(find .cache/apk/ -name APKINDEX.* -mtime +3)"
if [ -n "$old" ] || ! ls .cache/apk/APKINDEX.*; then
    buildah run --user root $ctr -- apk update
else
    echo Cache recent enough, skipping index update.
fi
buildah run --user root $ctr -- apk upgrade
buildah run --user root $ctr -- apk add bash