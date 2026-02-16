from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # HOME / AUTH
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('graficos/', views.dashboard_graficos, name='dashboard_graficos'),

    # # MODULOS (con prefijo)
    path('ventas/', include('ventas.urls')),
    path('productos/', include('productos.urls')),  
    path('compras/', include('compras.urls')),
    path('clientes/', include('clientes.urls')),
    path('proveedores/', include('proveedores.urls')),
    path('empleados/', include('empleados.urls')),
    path('configuracion/', include('configuracion.urls')),
    path('cai/', include('cai.urls')),
    path('cotizaciones/', include('cotizaciones.urls')),
    path('cuentas/', include('cuentas.urls')),
    path('caja/', include(('caja.urls', 'caja'), namespace='caja')),


    # AJAX (por ahora puede quedarse en core)
    path('crear-producto-ajax/', views.crear_producto_ajax, name='crear_producto_ajax'),
    path('crear-proveedor-ajax/', views.crear_proveedor_ajax, name='crear_proveedor_ajax'),
    path('sugerencias-productos/', views.sugerencias_productos, name='sugerencias_productos'),
    path('sugerencias-proveedores/', views.sugerencias_proveedores, name='sugerencias_proveedores'),
    path('crear-cliente-ajax/', views.crear_cliente_ajax, name='crear_cliente_ajax'),
    path('sugerencias-clientes/', views.sugerencias_clientes, name='sugerencias_clientes'),

]



