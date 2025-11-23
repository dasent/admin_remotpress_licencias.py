import streamlit as st
import requests
import random
import string

# ================== UTILIDAD RERUN (fiesta anti-bug) ================== #
def do_rerun():
    """Compatibilidad para actualizar la página en cualquier versión de Streamlit."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


# ================== CONFIG GENERAL ================== #

st.set_page_config(
    page_title="Admin Licencias RemotPress",
    page_icon="🔑",
    layout="wide",
)

# Estado inicial
if "base_url" not in st.session_state:
    st.session_state.base_url = "https://remotpress-licencias-api.onrender.com"
if "admin_key" not in st.session_state:
    st.session_state.admin_key = ""
if "dist_seleccionado" not in st.session_state:
    st.session_state.dist_seleccionado = None


# ================== HELPERS HTTP ================== #

def build_url(path: str) -> str:
    base = st.session_state.base_url.strip().rstrip("/")
    return f"{base}{path}"


def admin_headers() -> dict:
    return {"X-API-Key": st.session_state.admin_key.strip()} if st.session_state.admin_key else {}


def call_api(
    method: str,
    path: str,
    *,
    data: dict | None = None,
    json_body: dict | None = None,
    params: dict | None = None,
) -> requests.Response:
    url = build_url(path)
    headers = admin_headers()
    return requests.request(method, url, headers=headers, data=data, json=json_body, params=params, timeout=20)


def generar_api_key_aleatoria(nombre: str) -> str:
    sufijo = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"RMT-API-{nombre.upper()}-{sufijo}"


# ================== SIDEBAR CONFIG ================== #

with st.sidebar:
    st.header("⚙️ Configuración")

    st.session_state.base_url = st.text_input(
        "Base URL de la API",
        value=st.session_state.base_url,
        help="Ej: https://remotpress-licencias-api.onrender.com",
    )

    st.session_state.admin_key = st.text_input(
        "API Key de ADMIN",
        value=st.session_state.admin_key,
        type="password",
        help="API Key de tu usuario admin (dasent).",
    )

    if st.button("Probar conexión", use_container_width=True):
        try:
            r = call_api("GET", "/api/ping")
            if r.status_code == 200:
                datos = r.json()
                st.success(f"Conectado ✅  Versión API: {datos.get('version', '??')}")
            else:
                st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"No se pudo conectar: {e}")


# ================== UI PRINCIPAL ================== #

st.title("🔑 Panel Admin - Licencias RemotPress")
st.caption("Panel para administrar distribuidores y licencias usando tu API existente, sin tocar JSON.")

tab_crear, tab_listar = st.tabs(
    ["➕ Crear distribuidor", "📋 Listar y gestionar distribuidores"]
)

# --------------------------------------------------------------------- #
# TAB 1 – CREAR DISTRIBUIDOR
# --------------------------------------------------------------------- #
with tab_crear:
    st.subheader("Crear nuevo distribuidor")

    with st.form("form_crear_distribuidor"):
        col1, col2 = st.columns(2)

        with col1:
            nombre = st.text_input(
                "Nombre de usuario del distribuidor",
                placeholder="ej: TCNOMATIC_01",
            )
            clave = st.text_input(
                "Clave interna",
                placeholder="Contraseña o clave para tu control interno",
                type="password",
            )

        with col2:
            st.markdown("**Límites de licencias:**")
            limite_1 = st.number_input(
                "Licencias de 1 mes",
                min_value=0,
                value=10,
                step=1,
            )
            limite_3 = st.number_input(
                "Licencias de 3 meses",
                min_value=0,
                value=1,
                step=1,
            )
            limite_12 = st.number_input(
                "Licencias de 12 meses",
                min_value=0,
                value=1,
                step=1,
            )

        st.markdown("Si NO llenas la API Key, se generará automáticamente.")
        api_key_manual = st.text_input(
            "API Key (opcional)",
            placeholder="Déjalo vacío para generar una automática",
        )

        enviado = st.form_submit_button("Crear distribuidor")

    if enviado:
        if not nombre.strip() or not clave.strip():
            st.error("Nombre y clave son obligatorios.")
        else:
            api_key_final = api_key_manual.strip() or generar_api_key_aleatoria(nombre)
            try:
                # El endpoint en FastAPI está definido con Form(...), así que usamos data=
                payload = {
                    "nombre": nombre.strip(),
                    "clave": clave.strip(),
                    "api_key_nueva": api_key_final,
                    "limite_1": int(limite_1),
                    "limite_3": int(limite_3),
                    "limite_12": int(limite_12),
                }
                r = call_api("POST", "/api/admin/crear_distribuidor", data=payload)
                if r.status_code == 200:
                    data = r.json()
                    st.success("✅ Distribuidor creado correctamente.")
                    st.code(f"API Key: {data.get('api_key', api_key_final)}", language="text")
                    st.info("Guárdala y envíasela a tu distribuidor. Con esa API Key ya puede usar la API.")
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Error al llamar a la API: {e}")


# --------------------------------------------------------------------- #
# TAB 2 – LISTAR Y GESTIONAR DISTRIBUIDORES
# --------------------------------------------------------------------- #
with tab_listar:
    st.subheader("Distribuidores registrados")

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Actualizar lista"):
            st.session_state.dist_seleccionado = None
            do_rerun()

    # Si no hay seleccion actual, mostramos tabla de todos
    if st.session_state.dist_seleccionado is None:
        try:
            r = call_api("GET", "/api/admin/listar_distribuidores")
            if r.status_code != 200:
                st.error(f"Error al listar distribuidores ({r.status_code}): {r.text}")
            else:
                data = r.json()  # se espera lista de dicts
                if not data:
                    st.info("No hay distribuidores registrados todavía.")
                else:
                    for dist in data:
                        with st.container(border=True):
                            cols = st.columns([3, 3, 2, 2])
                            nombre = dist.get("nombre") or dist.get("user") or "??"
                            api_key = dist.get("api_key", "—")
                            bloqueado = dist.get("bloqueado", False)
                            limites = dist.get("limites", {})
                            usados = dist.get("usados", {})

                            estado_txt = "🔴 BLOQUEADO" if bloqueado else "🟢 ACTIVO"

                            with cols[0]:
                                st.markdown(f"**{nombre}**")
                                st.caption(estado_txt)

                            with cols[1]:
                                st.caption("API Key")
                                st.code(api_key, language="text")

                            with cols[2]:
                                st.caption("Límites")
                                st.write(
                                    f"1M: {limites.get(1, 0)} | "
                                    f"3M: {limites.get(3, 0)} | "
                                    f"12M: {limites.get(12, 0)}"
                                )

                            with cols[3]:
                                st.caption("Usadas")
                                st.write(
                                    f"1M: {usados.get(1, 0)} | "
                                    f"3M: {usados.get(3, 0)} | "
                                    f"12M: {usados.get(12, 0)}"
                                )
                                if st.button(
                                    "Ver detalles",
                                    key=f"btn_ver_{nombre}",
                                    use_container_width=True,
                                ):
                                    st.session_state.dist_seleccionado = nombre
                                    do_rerun()
        except Exception as e:
            st.error(f"Error al listar distribuidores: {e}")

    # Si ya hay uno seleccionado, mostramos detalle
    else:
        nombre = st.session_state.dist_seleccionado
        st.markdown(f"### Detalles de distribuidor: `{nombre}`")

        try:
            r = call_api("GET", "/api/admin/listar_distribuidores")
            if r.status_code != 200:
                st.error(f"Error al obtener datos del distribuidor ({r.status_code}): {r.text}")
            else:
                lista = r.json()
                dist = next((d for d in lista if d.get("nombre") == nombre or d.get("user") == nombre), None)
                if not dist:
                    st.error("No se encontró el distribuidor (puede que haya sido eliminado).")
                else:
                    api_key = dist.get("api_key", "—")
                    bloqueado = dist.get("bloqueado", False)
                    limites = dist.get("limites", {})
                    usados = dist.get("usados", {})

                    st.markdown(f"**API Key:** `{api_key}`")

                    col_estado, col_botones = st.columns([1, 1])
                    with col_estado:
                        if bloqueado:
                            st.success("Estado: 🔴 BLOQUEADO")
                        else:
                            st.success("Estado: 🟢 ACTIVO")

                    with col_botones:
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            txt_btn_block = "Desbloquear" if bloqueado else "Bloquear"
                            if st.button(txt_btn_block, type="primary", use_container_width=True):
                                try:
                                    payload = {"nombre": nombre}
                                    r2 = call_api("POST", "/api/admin/toggle_bloqueo", data=payload)
                                    if r2.status_code == 200:
                                        st.success("Estado actualizado.")
                                        do_rerun()
                                    else:
                                        st.error(f"Error {r2.status_code}: {r2.text}")
                                except Exception as e:
                                    st.error(f"Error al cambiar estado: {e}")

                        with col_b2:
                            if st.button("Eliminar", use_container_width=True):
                                try:
                                    payload = {"nombre": nombre}
                                    r3 = call_api("POST", "/api/admin/eliminar_distribuidor", data=payload)
                                    if r3.status_code == 200:
                                        st.success("Distribuidor eliminado.")
                                        st.session_state.dist_seleccionado = None
                                        do_rerun()
                                    else:
                                        st.error(f"Error {r3.status_code}: {r3.text}")
                                except Exception as e:
                                    st.error(f"Error al eliminar: {e}")

                    col_lim, col_usa = st.columns(2)

                    with col_lim:
                        st.markdown("#### Límites:")
                        st.write(f"1 mes(es): {limites.get(1, 0)} licencias")
                        st.write(f"3 mes(es): {limites.get(3, 0)} licencias")
                        st.write(f"12 mes(es): {limites.get(12, 0)} licencias")

                    with col_usa:
                        st.markdown("#### Usadas:")
                        st.write(f"1 mes(es): {usados.get(1, 0)} usadas")
                        st.write(f"3 mes(es): {usados.get(3, 0)} usadas")
                        st.write(f"12 mes(es): {usados.get(12, 0)} usadas")

                    st.divider()
                    if st.button("⬅ Volver a la lista"):
                        st.session_state.dist_seleccionado = None
                        do_rerun()
        except Exception as e:
            st.error(f"Error al cargar detalles: {e}")
