import streamlit as st
import requests

# ========================
# CONFIGURACIÓN BÁSICA
# ========================

st.set_page_config(
    page_title="Admin Licencias RemotPress",
    page_icon="🔑",
    layout="wide"
)

st.title("🔑 Panel Admin - Licencias RemotPress")

st.caption("Panel para administrar distribuidores y licencias usando tu API existente, sin tocar JSON.")

# URL base de tu API en Render
default_base_url = "https://remotpress-licencias-api.onrender.com"

if "base_url" not in st.session_state:
    st.session_state.base_url = default_base_url

if "admin_api_key" not in st.session_state:
    st.session_state.admin_api_key = ""

with st.sidebar:
    st.header("⚙️ Configuración")
    st.session_state.base_url = st.text_input(
        "Base URL de la API",
        value=st.session_state.base_url,
        help="Normalmente no cambia. Ej: https://remotpress-licencias-api.onrender.com"
    )
    st.session_state.admin_api_key = st.text_input(
        "API Key de ADMIN",
        value=st.session_state.admin_api_key,
        type="password",
        help="La API Key de tu usuario admin (ej: dasent)."
    )

    if st.button("Probar conexión"):
        try:
            r = requests.get(f"{st.session_state.base_url}/api/ping", timeout=10)
            if r.status_code == 200:
                st.success(f"Conectado ✅: {r.json()}")
            else:
                st.error(f"Error al conectar ({r.status_code}): {r.text}")
        except Exception as e:
            st.error(f"No se pudo conectar: {e}")


def admin_headers():
    return {
        "X-API-Key": st.session_state.admin_api_key or ""
    }


# ========================
# FUNCIONES AUXILIARES
# ========================

def crear_distribuidor_api(nombre, clave, limite_1, limite_3, limite_12):
    url = f"{st.session_state.base_url}/api/admin/crear_distribuidor"
    data = {
        "nombre": nombre,
        "clave": clave,
        "api_key_nueva": "",  # vacío para que la API genere una automáticamente
        "limite_1": limite_1,
        "limite_3": limite_3,
        "limite_12": limite_12
    }
    resp = requests.post(url, headers=admin_headers(), data=data, timeout=15)
    return resp


def listar_distribuidores_api():
    url = f"{st.session_state.base_url}/api/admin/distribuidores"
    resp = requests.get(url, headers=admin_headers(), timeout=15)
    return resp


def bloquear_api(nombre):
    url = f"{st.session_state.base_url}/api/admin/bloquear"
    resp = requests.post(url, headers=admin_headers(), data={"nombre": nombre}, timeout=15)
    return resp


def desbloquear_api(nombre):
    url = f"{st.session_state.base_url}/api/admin/desbloquear"
    resp = requests.post(url, headers=admin_headers(), data={"nombre": nombre}, timeout=15)
    return resp


def eliminar_api(nombre):
    url = f"{st.session_state.base_url}/api/admin/eliminar_distribuidor"
    resp = requests.post(url, headers=admin_headers(), data={"nombre": nombre}, timeout=15)
    return resp


# ========================
# UI PRINCIPAL - TABS
# ========================

tab_crear, tab_listar = st.tabs(["➕ Crear distribuidor", "📋 Listar y gestionar distribuidores"])

# --- TAB CREAR ---
with tab_crear:
    st.subheader("➕ Crear nuevo distribuidor")

    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre de usuario del distribuidor", placeholder="ej: tcnomatic2")
        clave = st.text_input("Clave interna (para registro futuro, si la usas)", value="123456")

    with col2:
        st.markdown("**Límites de licencias**")
        limite_1 = st.number_input("Licencias de 1 mes", min_value=0, value=30, step=1)
        limite_3 = st.number_input("Licencias de 3 meses", min_value=0, value=30, step=1)
        limite_12 = st.number_input("Licencias de 12 meses", min_value=0, value=30, step=1)

    st.info("La API Key se generará automáticamente. Solo debes indicar nombre, clave y límites.")

    if st.button("✅ Crear distribuidor"):
        if not st.session_state.admin_api_key:
            st.error("Debes configurar la API Key de ADMIN en la barra lateral.")
        elif not nombre.strip():
            st.error("El nombre de usuario no puede estar vacío.")
        else:
            with st.spinner("Creando distribuidor..."):
                try:
                    resp = crear_distribuidor_api(nombre.strip(), clave.strip(), limite_1, limite_3, limite_12)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success("Distribuidor creado correctamente.")
                        st.json(data)
                        st.markdown(
                            f"### 🔐 API Key generada para **{data.get('usuario')}**\n"
                            f"```text\n{data.get('api_key')}\n```"
                        )
                    else:
                        st.error(f"Error ({resp.status_code}): {resp.text}")
                except Exception as e:
                    st.error(f"Error al llamar a la API: {e}")

# --- TAB LISTAR ---
with tab_listar:
    st.subheader("📋 Distribuidores registrados")

    if st.button("🔄 Actualizar lista"):
        st.session_state["_force_reload"] = True

    # Cargar lista siempre (para que no sea tan confuso)
    try:
        resp = listar_distribuidores_api()
        if resp.status_code == 200:
            data = resp.json()
            distribuidores = data.get("distribuidores", [])
            if not distribuidores:
                st.warning("No hay distribuidores registrados aún.")
            else:
                st.success(f"Se encontraron {len(distribuidores)} distribuidores.")
                for dist in distribuidores:
                    usuario = dist.get("usuario")
                    api_key = dist.get("api_key")
                    bloqueado = dist.get("bloqueado", False)
                    limites = dist.get("limites", {})
                    usados = dist.get("usados", {})

                    exp = st.expander(
                        f"👤 {usuario}  |  {'⛔ BLOQUEADO' if bloqueado else '✅ ACTIVO'}",
                        expanded=False
                    )
                    with exp:
                        st.markdown(f"**API Key:** `{api_key}`")
                        st.markdown(f"**Estado:** {'⛔ BLOQUEADO' if bloqueado else '✅ ACTIVO'}")

                        colL, colR = st.columns(2)

                        with colL:
                            st.markdown("**Límites:**")
                            if limites:
                                for k, v in limites.items():
                                    st.write(f"- {k} mes(es): {v} licencias")
                            else:
                                st.write("_Sin límites configurados_")

                        with colR:
                            st.markdown("**Usadas:**")
                            if usados:
                                for k, v in usados.items():
                                    st.write(f"- {k} mes(es): {v} usadas")
                            else:
                                st.write("_Sin usos registrados_")

                        col_btn1, col_btn2, col_btn3 = st.columns(3)

                        with col_btn1:
                            if not bloqueado:
                                if st.button("⛔ Bloquear", key=f"bloq_{usuario}"):
                                    try:
                                        r = bloquear_api(usuario)
                                        if r.status_code == 200:
                                            st.success("Usuario bloqueado.")
                                            st.experimental_rerun()
                                        else:
                                            st.error(f"Error: {r.text}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            else:
                                if st.button("✅ Desbloquear", key=f"desb_{usuario}"):
                                    try:
                                        r = desbloquear_api(usuario)
                                        if r.status_code == 200:
                                            st.success("Usuario desbloqueado.")
                                            st.experimental_rerun()
                                        else:
                                            st.error(f"Error: {r.text}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                        with col_btn2:
                            st.write("")

                        with col_btn3:
                            if st.button("🗑 Eliminar", key=f"elim_{usuario}"):
                                try:
                                    r = eliminar_api(usuario)
                                    if r.status_code == 200:
                                        st.success("Usuario eliminado.")
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"Error: {r.text}")
                                except Exception as e:
                                    st.error(f"Error: {e}")
        else:
            st.error(f"Error al listar distribuidores ({resp.status_code}): {resp.text}")
    except Exception as e:
        st.error(f"No se pudo cargar la lista de distribuidores: {e}")
