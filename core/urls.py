# AGREGA ESTAS URLs a tu core/urls.py EXISTENTE:

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # URLs existentes que ya tienes...
    path('', views.dashboard, name='dashboard'),  # Redirigir a dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    
    # Productos
    path('productos/', views.listar_productos, name='listar_productos'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    path('sugerencias-productos/', views.sugerencias_productos, name='sugerencias_productos'),

    # Ventas (CORREGIR ESTAS RUTAS)
    path('ventas/crear/', views.crear_venta, name='crear_venta'),
    path('crear-venta/', views.crear_venta, name='crear_venta'),
    path('ventas/', views.resumen_ventas, name='resumen_ventas'),
    path('buscar-producto/', views.buscar_producto, name='buscar_producto'),  # ✅ NUEVA
    path('factura/<int:venta_id>/', views.factura, name='factura'),
    path('buscar-producto-id/', views.buscar_producto_id, name='buscar_producto_id'),
    
    # Cotizaciones
    path('cotizaciones/', views.lista_cotizaciones, name='lista_cotizaciones'),
    path('cotizaciones/nueva/', views.crear_cotizacion, name='crear_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/', views.detalle_cotizacion, name='detalle_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/facturar/', views.facturar_cotizacion, name='facturar_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/editar/', views.editar_cotizacion, name='editar_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/eliminar/', views.eliminar_cotizacion, name='eliminar_cotizacion'),

    # Compras
    path('crear-compra/', views.crear_compra, name='crear_compra'),
    path('compras/', views.resumen_compras, name='resumen_compras'),
    path('compra/<int:compra_id>/', views.resumen_compra, name='resumen_compra'),
    
    # Clientes
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('buscar-clientes/', views.buscar_clientes, name='buscar_clientes'),

    # Proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/registrar/', views.registrar_proveedor, name='registrar_proveedor'),
    
    # CAI
    path('cai/', views.listar_cai, name='listar_cai'),
    path('cai/crear/', views.crear_cai, name='crear_cai'),
    path('cai/editar/<int:pk>/', views.editar_cai, name='editar_cai'),
    path('cai/eliminar/<int:pk>/', views.eliminar_cai, name='eliminar_cai'),
    
    # Cuentas
    path('cuentas/', views.resumen_cuentas, name='resumen_cuentas'),
    path('pago-cliente/<int:cuenta_id>/', views.registrar_pago_cliente, name='registrar_pago_cliente'),
    path('pago-proveedor/<int:cuenta_id>/', views.registrar_pago_proveedor, name='registrar_pago_proveedor'),
    
    # Gráficos
    path('graficos/', views.dashboard_graficos, name='dashboard_graficos'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Empleados y Pagos
    path("empleados/", views.lista_empleados, name="lista_empleados"),
    path("empleados/nuevo/", views.crear_empleado, name="crear_empleado"),
    path("empleados/<int:pk>/editar/", views.editar_empleado, name="editar_empleado"),
    path("empleados/pagos/", views.lista_pagos, name="lista_pagos"),
    path("empleados/pagos/nuevo/", views.registrar_pago, name="registrar_pago"),
    
    # EMPRESA
    path('configuracion-empresa/', views.configuracion_empresa, name='configuracion_empresa'),

    
    
]

