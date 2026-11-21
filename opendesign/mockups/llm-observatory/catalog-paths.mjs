const part = "[A-Za-z0-9_][A-Za-z0-9_.-]*";
export const modelIdPattern = new RegExp(`^${part}/${part}$`);
export const runtimeIdPattern = /^[a-z][a-z0-9.-]*$/;
export const hardwareIdPattern = /^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/;
export const catalogReleasePattern = /^v1-[a-f0-9]{16}$/;

export function deniedCatalogPin(release, paths) {
  return ["catalog", "catalog-data"].some(kind => {
    const prefix = `/${kind}/${release}`;
    return paths.some(path => path === prefix || path.startsWith(prefix + "/") || path === `/${kind}/*`);
  });
}

export function catalogPath(release, kind, id, extension = "html") {
  return `catalog/${release}/${kind}/${id}.${extension}`;
}

export function modelShard(id) {
  return id.split("/")[0].slice(0, 2).toLowerCase();
}
