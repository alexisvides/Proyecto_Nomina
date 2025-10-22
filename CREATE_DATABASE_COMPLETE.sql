USE [master]
GO
/****** Object:  Database [proyecto]    Script Date: 21/10/2025 22:41:16 ******/
CREATE DATABASE [proyecto]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'proyecto', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL16.SQLSERVER\MSSQL\DATA\proyecto.mdf' , SIZE = 73728KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'proyecto_log', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL16.SQLSERVER\MSSQL\DATA\proyecto_log.ldf' , SIZE = 73728KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
 WITH CATALOG_COLLATION = DATABASE_DEFAULT, LEDGER = OFF
GO
ALTER DATABASE [proyecto] SET COMPATIBILITY_LEVEL = 160
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [proyecto].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [proyecto] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [proyecto] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [proyecto] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [proyecto] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [proyecto] SET ARITHABORT OFF 
GO
ALTER DATABASE [proyecto] SET AUTO_CLOSE OFF 
GO
ALTER DATABASE [proyecto] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [proyecto] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [proyecto] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [proyecto] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [proyecto] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [proyecto] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [proyecto] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [proyecto] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [proyecto] SET  ENABLE_BROKER 
GO
ALTER DATABASE [proyecto] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [proyecto] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [proyecto] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [proyecto] SET ALLOW_SNAPSHOT_ISOLATION OFF 
GO
ALTER DATABASE [proyecto] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [proyecto] SET READ_COMMITTED_SNAPSHOT OFF 
GO
ALTER DATABASE [proyecto] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [proyecto] SET RECOVERY FULL 
GO
ALTER DATABASE [proyecto] SET  MULTI_USER 
GO
ALTER DATABASE [proyecto] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [proyecto] SET DB_CHAINING OFF 
GO
ALTER DATABASE [proyecto] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
GO
ALTER DATABASE [proyecto] SET TARGET_RECOVERY_TIME = 60 SECONDS 
GO
ALTER DATABASE [proyecto] SET DELAYED_DURABILITY = DISABLED 
GO
ALTER DATABASE [proyecto] SET ACCELERATED_DATABASE_RECOVERY = OFF  
GO
EXEC sys.sp_db_vardecimal_storage_format N'proyecto', N'ON'
GO
ALTER DATABASE [proyecto] SET QUERY_STORE = ON
GO
ALTER DATABASE [proyecto] SET QUERY_STORE (OPERATION_MODE = READ_WRITE, CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30), DATA_FLUSH_INTERVAL_SECONDS = 900, INTERVAL_LENGTH_MINUTES = 60, MAX_STORAGE_SIZE_MB = 1000, QUERY_CAPTURE_MODE = AUTO, SIZE_BASED_CLEANUP_MODE = AUTO, MAX_PLANS_PER_QUERY = 200, WAIT_STATS_CAPTURE_MODE = ON)
GO
USE [proyecto]
GO
/****** Object:  Table [dbo].[Asistencias]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Asistencias](
	[IdAsistencia] [int] IDENTITY(1,1) NOT NULL,
	[IdEmpleado] [int] NOT NULL,
	[FechaHora] [datetime2](7) NOT NULL,
	[Tipo] [varchar](20) NOT NULL,
	[Observacion] [varchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[IdAsistencia] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Auditoria]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Auditoria](
	[IdLog] [int] IDENTITY(1,1) NOT NULL,
	[IdUsuario] [int] NULL,
	[NombreUsuario] [varchar](50) NULL,
	[Accion] [varchar](100) NOT NULL,
	[Modulo] [varchar](50) NULL,
	[Detalles] [varchar](500) NULL,
	[FechaHora] [datetime2](7) NOT NULL,
	[DireccionIP] [varchar](45) NULL,
PRIMARY KEY CLUSTERED 
(
	[IdLog] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[BeneficiosDeducciones]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[BeneficiosDeducciones](
	[IdBeneficioDeduccion] [int] IDENTITY(1,1) NOT NULL,
	[Nombre] [varchar](120) NOT NULL,
	[Tipo] [varchar](20) NOT NULL,
	[TipoCalculo] [varchar](20) NOT NULL,
	[Valor] [decimal](10, 4) NULL,
	[Activo] [bit] NOT NULL,
	[Descripcion] [varchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[IdBeneficioDeduccion] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Departamentos]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Departamentos](
	[IdDepartamento] [int] IDENTITY(1,1) NOT NULL,
	[Nombre] [varchar](100) NOT NULL,
	[Descripcion] [varchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[IdDepartamento] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[Nombre] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DocumentosEmpleado]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DocumentosEmpleado](
	[IdDocumento] [int] IDENTITY(1,1) NOT NULL,
	[IdEmpleado] [int] NOT NULL,
	[TipoDocumento] [varchar](50) NOT NULL,
	[RutaArchivo] [varchar](255) NOT NULL,
	[FechaCarga] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdDocumento] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[EmpleadoBeneficioDeduccion]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[EmpleadoBeneficioDeduccion](
	[IdEmpleadoBD] [int] IDENTITY(1,1) NOT NULL,
	[IdEmpleado] [int] NOT NULL,
	[IdBeneficioDeduccion] [int] NOT NULL,
	[ValorPersonalizado] [decimal](12, 2) NULL,
	[Activo] [bit] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdEmpleadoBD] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[EmpleadoBeneficios]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[EmpleadoBeneficios](
	[IdEmpleado] [int] NOT NULL,
	[IdBeneficioDeduccion] [int] NOT NULL,
	[Activo] [bit] NOT NULL,
	[TipoCalculo] [varchar](20) NULL,
	[Valor] [decimal](18, 4) NULL,
 CONSTRAINT [PK_EmpleadoBeneficios] PRIMARY KEY CLUSTERED 
(
	[IdEmpleado] ASC,
	[IdBeneficioDeduccion] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Empleados]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Empleados](
	[IdEmpleado] [int] IDENTITY(1,1) NOT NULL,
	[CodigoEmpleado] [varchar](30) NOT NULL,
	[Nombres] [varchar](100) NOT NULL,
	[Apellidos] [varchar](100) NOT NULL,
	[DocumentoIdentidad] [varchar](50) NOT NULL,
	[FechaContratacion] [date] NOT NULL,
	[IdDepartamento] [int] NULL,
	[IdPuesto] [int] NULL,
	[SalarioBase] [decimal](12, 2) NOT NULL,
	[Correo] [varchar](150) NULL,
	[Telefono] [varchar](30) NULL,
	[TipoContrato] [varchar](50) NULL,
	[FechaCreacion] [datetime2](7) NOT NULL,
	[FechaActualizacion] [datetime2](7) NULL,
	[ActualizadoPor] [int] NULL,
	[NumeroIGSS] [varchar](50) NULL,
	[FechaFin] [date] NULL,
	[FechaNacimiento] [date] NULL,
PRIMARY KEY CLUSTERED 
(
	[IdEmpleado] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[DocumentoIdentidad] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[CodigoEmpleado] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[Correo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ItemsNomina]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ItemsNomina](
	[IdItem] [int] IDENTITY(1,1) NOT NULL,
	[IdNomina] [int] NOT NULL,
	[IdBeneficioDeduccion] [int] NULL,
	[TipoItem] [varchar](20) NOT NULL,
	[Monto] [decimal](12, 2) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdItem] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Modulos]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Modulos](
	[IdModulo] [int] IDENTITY(1,1) NOT NULL,
	[Nombre] [varchar](50) NOT NULL,
	[Descripcion] [varchar](255) NULL,
	[Ruta] [varchar](100) NOT NULL,
	[Icono] [varchar](50) NULL,
	[Orden] [int] NOT NULL,
	[Activo] [bit] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdModulo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[Nombre] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[PeriodosNomina]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[PeriodosNomina](
	[IdPeriodo] [int] IDENTITY(1,1) NOT NULL,
	[FechaInicio] [date] NOT NULL,
	[FechaFin] [date] NOT NULL,
	[TipoPeriodo] [varchar](20) NOT NULL,
	[FechaCreacion] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdPeriodo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_PeriodosNomina] UNIQUE NONCLUSTERED 
(
	[FechaInicio] ASC,
	[FechaFin] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[PermisosUsuarios]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[PermisosUsuarios](
	[IdPermiso] [int] IDENTITY(1,1) NOT NULL,
	[IdUsuario] [int] NOT NULL,
	[IdModulo] [int] NOT NULL,
	[TieneAcceso] [bit] NOT NULL,
	[PuedeCrear] [bit] NOT NULL,
	[PuedeEditar] [bit] NOT NULL,
	[PuedeEliminar] [bit] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdPermiso] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[IdUsuario] ASC,
	[IdModulo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[PlantillasPermisos]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[PlantillasPermisos](
	[IdPlantilla] [int] IDENTITY(1,1) NOT NULL,
	[Nombre] [varchar](100) NOT NULL,
	[Descripcion] [varchar](255) NULL,
	[Activo] [bit] NOT NULL,
	[FechaCreacion] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdPlantilla] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[Nombre] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[PlantillasPermisosDetalle]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[PlantillasPermisosDetalle](
	[IdDetalle] [int] IDENTITY(1,1) NOT NULL,
	[IdPlantilla] [int] NOT NULL,
	[IdModulo] [int] NOT NULL,
	[TieneAcceso] [bit] NOT NULL,
	[PuedeCrear] [bit] NOT NULL,
	[PuedeEditar] [bit] NOT NULL,
	[PuedeEliminar] [bit] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdDetalle] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[IdPlantilla] ASC,
	[IdModulo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Puestos]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Puestos](
	[IdPuesto] [int] IDENTITY(1,1) NOT NULL,
	[IdDepartamento] [int] NULL,
	[Titulo] [varchar](100) NOT NULL,
	[Descripcion] [varchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[IdPuesto] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RegistrosNomina]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RegistrosNomina](
	[IdNomina] [int] IDENTITY(1,1) NOT NULL,
	[IdEmpleado] [int] NOT NULL,
	[IdPeriodo] [int] NOT NULL,
	[SalarioBase] [decimal](12, 2) NOT NULL,
	[TotalPrestaciones] [decimal](12, 2) NOT NULL,
	[TotalDeducciones] [decimal](12, 2) NOT NULL,
	[SalarioNeto] [decimal](12, 2) NOT NULL,
	[FechaGeneracion] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdNomina] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_RegistrosNomina] UNIQUE NONCLUSTERED 
(
	[IdEmpleado] ASC,
	[IdPeriodo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Roles]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Roles](
	[IdRol] [int] IDENTITY(1,1) NOT NULL,
	[Nombre] [varchar](50) NOT NULL,
	[Descripcion] [varchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[IdRol] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[Nombre] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[UsuarioRol]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[UsuarioRol](
	[IdUsuario] [int] NOT NULL,
	[IdRol] [int] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[IdUsuario] ASC,
	[IdRol] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Usuarios]    Script Date: 21/10/2025 22:41:16 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Usuarios](
	[IdUsuario] [int] IDENTITY(1,1) NOT NULL,
	[NombreUsuario] [varchar](50) NOT NULL,
	[Correo] [varchar](150) NOT NULL,
	[ClaveHash] [varchar](255) NOT NULL,
	[Activo] [bit] NOT NULL,
	[FechaCreacion] [datetime2](7) NOT NULL,
	[FechaActualizacion] [datetime2](7) NULL,
	[ActualizadoPor] [int] NULL,
	[IdRol] [int] NULL,
	[IdEmpleado] [int] NULL,
PRIMARY KEY CLUSTERED 
(
	[IdUsuario] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[Correo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[NombreUsuario] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Index [IX_Asistencias_FechaHora]    Script Date: 21/10/2025 22:41:16 ******/
CREATE NONCLUSTERED INDEX [IX_Asistencias_FechaHora] ON [dbo].[Asistencias]
(
	[FechaHora] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Asistencias_IdEmpleado]    Script Date: 21/10/2025 22:41:16 ******/
CREATE NONCLUSTERED INDEX [IX_Asistencias_IdEmpleado] ON [dbo].[Asistencias]
(
	[IdEmpleado] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Auditoria_FechaHora]    Script Date: 21/10/2025 22:41:16 ******/
CREATE NONCLUSTERED INDEX [IX_Auditoria_FechaHora] ON [dbo].[Auditoria]
(
	[FechaHora] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Auditoria_Usuario]    Script Date: 21/10/2025 22:41:16 ******/
CREATE NONCLUSTERED INDEX [IX_Auditoria_Usuario] ON [dbo].[Auditoria]
(
	[IdUsuario] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_EB_Beneficio]    Script Date: 21/10/2025 22:41:16 ******/
CREATE NONCLUSTERED INDEX [IX_EB_Beneficio] ON [dbo].[EmpleadoBeneficios]
(
	[IdBeneficioDeduccion] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Empleados_NumeroIGSS]    Script Date: 21/10/2025 22:41:16 ******/
CREATE NONCLUSTERED INDEX [IX_Empleados_NumeroIGSS] ON [dbo].[Empleados]
(
	[NumeroIGSS] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Usuarios_IdEmpleado]    Script Date: 21/10/2025 22:41:16 ******/
CREATE NONCLUSTERED INDEX [IX_Usuarios_IdEmpleado] ON [dbo].[Usuarios]
(
	[IdEmpleado] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[Asistencias] ADD  CONSTRAINT [DF_Asistencias_FechaHora]  DEFAULT (getdate()) FOR [FechaHora]
GO
ALTER TABLE [dbo].[Auditoria] ADD  DEFAULT (getdate()) FOR [FechaHora]
GO
ALTER TABLE [dbo].[BeneficiosDeducciones] ADD  DEFAULT ((1)) FOR [Activo]
GO
ALTER TABLE [dbo].[DocumentosEmpleado] ADD  DEFAULT (getdate()) FOR [FechaCarga]
GO
ALTER TABLE [dbo].[EmpleadoBeneficioDeduccion] ADD  DEFAULT ((1)) FOR [Activo]
GO
ALTER TABLE [dbo].[EmpleadoBeneficios] ADD  DEFAULT ((1)) FOR [Activo]
GO
ALTER TABLE [dbo].[Empleados] ADD  DEFAULT (getdate()) FOR [FechaCreacion]
GO
ALTER TABLE [dbo].[Modulos] ADD  DEFAULT ((0)) FOR [Orden]
GO
ALTER TABLE [dbo].[Modulos] ADD  DEFAULT ((1)) FOR [Activo]
GO
ALTER TABLE [dbo].[PeriodosNomina] ADD  DEFAULT (getdate()) FOR [FechaCreacion]
GO
ALTER TABLE [dbo].[PermisosUsuarios] ADD  DEFAULT ((1)) FOR [TieneAcceso]
GO
ALTER TABLE [dbo].[PermisosUsuarios] ADD  DEFAULT ((1)) FOR [PuedeCrear]
GO
ALTER TABLE [dbo].[PermisosUsuarios] ADD  DEFAULT ((1)) FOR [PuedeEditar]
GO
ALTER TABLE [dbo].[PermisosUsuarios] ADD  DEFAULT ((1)) FOR [PuedeEliminar]
GO
ALTER TABLE [dbo].[PlantillasPermisos] ADD  DEFAULT ((1)) FOR [Activo]
GO
ALTER TABLE [dbo].[PlantillasPermisos] ADD  DEFAULT (getdate()) FOR [FechaCreacion]
GO
ALTER TABLE [dbo].[PlantillasPermisosDetalle] ADD  DEFAULT ((1)) FOR [TieneAcceso]
GO
ALTER TABLE [dbo].[PlantillasPermisosDetalle] ADD  DEFAULT ((1)) FOR [PuedeCrear]
GO
ALTER TABLE [dbo].[PlantillasPermisosDetalle] ADD  DEFAULT ((1)) FOR [PuedeEditar]
GO
ALTER TABLE [dbo].[PlantillasPermisosDetalle] ADD  DEFAULT ((1)) FOR [PuedeEliminar]
GO
ALTER TABLE [dbo].[RegistrosNomina] ADD  DEFAULT ((0)) FOR [TotalPrestaciones]
GO
ALTER TABLE [dbo].[RegistrosNomina] ADD  DEFAULT ((0)) FOR [TotalDeducciones]
GO
ALTER TABLE [dbo].[RegistrosNomina] ADD  DEFAULT ((0)) FOR [SalarioNeto]
GO
ALTER TABLE [dbo].[RegistrosNomina] ADD  DEFAULT (getdate()) FOR [FechaGeneracion]
GO
ALTER TABLE [dbo].[Usuarios] ADD  DEFAULT ((1)) FOR [Activo]
GO
ALTER TABLE [dbo].[Usuarios] ADD  DEFAULT (getdate()) FOR [FechaCreacion]
GO
ALTER TABLE [dbo].[Asistencias]  WITH CHECK ADD  CONSTRAINT [FK_Asistencias_Empleados] FOREIGN KEY([IdEmpleado])
REFERENCES [dbo].[Empleados] ([IdEmpleado])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[Asistencias] CHECK CONSTRAINT [FK_Asistencias_Empleados]
GO
ALTER TABLE [dbo].[Auditoria]  WITH CHECK ADD FOREIGN KEY([IdUsuario])
REFERENCES [dbo].[Usuarios] ([IdUsuario])
ON DELETE SET NULL
GO
ALTER TABLE [dbo].[DocumentosEmpleado]  WITH CHECK ADD FOREIGN KEY([IdEmpleado])
REFERENCES [dbo].[Empleados] ([IdEmpleado])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[EmpleadoBeneficioDeduccion]  WITH CHECK ADD FOREIGN KEY([IdBeneficioDeduccion])
REFERENCES [dbo].[BeneficiosDeducciones] ([IdBeneficioDeduccion])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[EmpleadoBeneficioDeduccion]  WITH CHECK ADD FOREIGN KEY([IdEmpleado])
REFERENCES [dbo].[Empleados] ([IdEmpleado])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[EmpleadoBeneficios]  WITH CHECK ADD  CONSTRAINT [FK_EB_Beneficio] FOREIGN KEY([IdBeneficioDeduccion])
REFERENCES [dbo].[BeneficiosDeducciones] ([IdBeneficioDeduccion])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[EmpleadoBeneficios] CHECK CONSTRAINT [FK_EB_Beneficio]
GO
ALTER TABLE [dbo].[EmpleadoBeneficios]  WITH CHECK ADD  CONSTRAINT [FK_EB_Empleado] FOREIGN KEY([IdEmpleado])
REFERENCES [dbo].[Empleados] ([IdEmpleado])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[EmpleadoBeneficios] CHECK CONSTRAINT [FK_EB_Empleado]
GO
ALTER TABLE [dbo].[Empleados]  WITH CHECK ADD FOREIGN KEY([ActualizadoPor])
REFERENCES [dbo].[Usuarios] ([IdUsuario])
GO
ALTER TABLE [dbo].[Empleados]  WITH CHECK ADD FOREIGN KEY([IdDepartamento])
REFERENCES [dbo].[Departamentos] ([IdDepartamento])
ON DELETE SET NULL
GO
ALTER TABLE [dbo].[Empleados]  WITH CHECK ADD FOREIGN KEY([IdPuesto])
REFERENCES [dbo].[Puestos] ([IdPuesto])
ON DELETE SET NULL
GO
ALTER TABLE [dbo].[ItemsNomina]  WITH CHECK ADD FOREIGN KEY([IdBeneficioDeduccion])
REFERENCES [dbo].[BeneficiosDeducciones] ([IdBeneficioDeduccion])
ON DELETE SET NULL
GO
ALTER TABLE [dbo].[ItemsNomina]  WITH CHECK ADD FOREIGN KEY([IdNomina])
REFERENCES [dbo].[RegistrosNomina] ([IdNomina])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[PermisosUsuarios]  WITH CHECK ADD FOREIGN KEY([IdModulo])
REFERENCES [dbo].[Modulos] ([IdModulo])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[PermisosUsuarios]  WITH CHECK ADD FOREIGN KEY([IdUsuario])
REFERENCES [dbo].[Usuarios] ([IdUsuario])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[PlantillasPermisosDetalle]  WITH CHECK ADD FOREIGN KEY([IdModulo])
REFERENCES [dbo].[Modulos] ([IdModulo])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[PlantillasPermisosDetalle]  WITH CHECK ADD FOREIGN KEY([IdPlantilla])
REFERENCES [dbo].[PlantillasPermisos] ([IdPlantilla])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[Puestos]  WITH CHECK ADD FOREIGN KEY([IdDepartamento])
REFERENCES [dbo].[Departamentos] ([IdDepartamento])
ON DELETE SET NULL
GO
ALTER TABLE [dbo].[RegistrosNomina]  WITH CHECK ADD FOREIGN KEY([IdEmpleado])
REFERENCES [dbo].[Empleados] ([IdEmpleado])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[RegistrosNomina]  WITH CHECK ADD FOREIGN KEY([IdPeriodo])
REFERENCES [dbo].[PeriodosNomina] ([IdPeriodo])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[UsuarioRol]  WITH CHECK ADD FOREIGN KEY([IdRol])
REFERENCES [dbo].[Roles] ([IdRol])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[UsuarioRol]  WITH CHECK ADD FOREIGN KEY([IdUsuario])
REFERENCES [dbo].[Usuarios] ([IdUsuario])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[Usuarios]  WITH CHECK ADD  CONSTRAINT [FK_Usuarios_Empleados] FOREIGN KEY([IdEmpleado])
REFERENCES [dbo].[Empleados] ([IdEmpleado])
GO
ALTER TABLE [dbo].[Usuarios] CHECK CONSTRAINT [FK_Usuarios_Empleados]
GO
ALTER TABLE [dbo].[Usuarios]  WITH CHECK ADD  CONSTRAINT [FK_Usuarios_Roles] FOREIGN KEY([IdRol])
REFERENCES [dbo].[Roles] ([IdRol])
ON DELETE SET NULL
GO
ALTER TABLE [dbo].[Usuarios] CHECK CONSTRAINT [FK_Usuarios_Roles]
GO
ALTER TABLE [dbo].[Asistencias]  WITH CHECK ADD  CONSTRAINT [CK_Asistencias_Tipo] CHECK  (([Tipo]='salida' OR [Tipo]='entrada'))
GO
ALTER TABLE [dbo].[Asistencias] CHECK CONSTRAINT [CK_Asistencias_Tipo]
GO
ALTER TABLE [dbo].[BeneficiosDeducciones]  WITH CHECK ADD CHECK  (([TipoCalculo]='fijo' OR [TipoCalculo]='porcentaje'))
GO
ALTER TABLE [dbo].[BeneficiosDeducciones]  WITH CHECK ADD CHECK  (([Valor]>=(0)))
GO
ALTER TABLE [dbo].[BeneficiosDeducciones]  WITH CHECK ADD CHECK  (([Tipo]='prestacion' OR [Tipo]='deduccion'))
GO
ALTER TABLE [dbo].[EmpleadoBeneficioDeduccion]  WITH CHECK ADD CHECK  (([ValorPersonalizado]>=(0)))
GO
ALTER TABLE [dbo].[Empleados]  WITH CHECK ADD CHECK  (([SalarioBase]>=(0)))
GO
ALTER TABLE [dbo].[ItemsNomina]  WITH CHECK ADD CHECK  (([Monto]>=(0)))
GO
ALTER TABLE [dbo].[ItemsNomina]  WITH CHECK ADD CHECK  (([TipoItem]='prestacion' OR [TipoItem]='deduccion'))
GO
ALTER TABLE [dbo].[PeriodosNomina]  WITH CHECK ADD CHECK  (([TipoPeriodo]='anual' OR [TipoPeriodo]='semanal' OR [TipoPeriodo]='quincenal' OR [TipoPeriodo]='mensual'))
GO
ALTER TABLE [dbo].[RegistrosNomina]  WITH CHECK ADD CHECK  (([SalarioBase]>=(0)))
GO
ALTER TABLE [dbo].[RegistrosNomina]  WITH CHECK ADD CHECK  (([TotalPrestaciones]>=(0)))
GO
ALTER TABLE [dbo].[RegistrosNomina]  WITH CHECK ADD CHECK  (([TotalDeducciones]>=(0)))
GO
USE [master]
GO
ALTER DATABASE [proyecto] SET  READ_WRITE 
GO
