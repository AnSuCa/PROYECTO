-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 28-05-2025 a las 21:15:00
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `cliente`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cliente`
--

CREATE TABLE `cliente` (
  `nombre` text NOT NULL,
  `apellido` text NOT NULL,
  `cedula` int(12) NOT NULL,
  `usuario` text NOT NULL,
  `categoria` text NOT NULL,
  `contraseña` varchar(12) NOT NULL,
  `items` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cliente`
--

INSERT INTO `cliente` (`nombre`, `apellido`, `cedula`, `usuario`, `categoria`, `contraseña`, `items`) VALUES
('pedro', '', 0, 'admon', '', '1234', ''),
('juan', '', 0, 'admin', '', '5678', ''),
('francisco', 'jimenez', 1015465091, 'fjimenez', 'admin', '12345', ''),
('juan', 'pardo', 12312321, 'jpardo', 'usuario', 'jpardo', ''),
('carlos', 'cardenaz', 12121314, 'ccardenaz', 'usuario', 'ccardenaz', ''),
('juan', 'cardenaz', 12121312, 'jcardenaz', 'admin', 'jcardenaz', '');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `items`
--

CREATE TABLE `items` (
  `nombre` text NOT NULL,
  `descripcion` text NOT NULL,
  `id` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `items`
--

INSERT INTO `items` (`nombre`, `descripcion`, `id`) VALUES
('torta', 'torta de chocolate', '5'),
('jugo', 'jugo de naranja', '7'),
('pai', 'pai de manzana', '2'),
('pai', 'pai de pera', '3'),
('torta', 'torta de yogurt', '1'),
('torta', 'torta de zanahoria', '4'),
('torta', 'torta de naranja', '6'),
('jugo', 'jugo de uva ', '8'),
('jugo ', 'jugo de manzana', '9'),
('jugo', 'jugo de fresa', '10'),
('torta', 'tortad', '11'),
('prueba', '', '');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
