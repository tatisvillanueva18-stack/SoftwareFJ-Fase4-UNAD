# modelos/servicio.py
from abc import abstractmethod
from modelos.entidad import EntidadSistema
from utilidades.excepciones import (
    ErrorValidacionDatos,
    ErrorServicioNoDisponible,
    ErrorOperacionNoPermitida
)
from utilidades.logger import GestorLogs


class Servicio(EntidadSistema):
    """
    Clase abstracta que representa un servicio ofrecido por Software FJ.
    Hereda de EntidadSistema e implementa polimorfismo para el cálculo de costos.
    """

    def __init__(self, id_entidad: str, nombre: str, tarifa_base: float, disponible: bool = True):
        # Inicializa los atributos heredados de EntidadSistema (id y fecha de creación)
        super().__init__(id_entidad)
        # Inicializa el gestor de auditoría para registrar eventos y errores
        self._logger = GestorLogs()
        # Asigna los atributos mediante setters para aplicar validaciones estrictas
        self.nombre = nombre
        self.tarifa_base = tarifa_base
        self.disponible = disponible

    # --- Propiedades y Encapsulación ---
    @property
    def nombre(self) -> str:
        """Retorna el nombre del servicio."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Valida que el nombre del servicio no esté vacío."""
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ErrorValidacionDatos("El nombre del servicio debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def tarifa_base(self) -> float:
        """Retorna la tarifa base por hora o unidad del servicio."""
        return self._tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor: float) -> None:
        """Valida que la tarifa base sea un número positivo mayor a cero."""
        if not isinstance(valor, (int, float)) or valor <= 0:
            raise ErrorValidacionDatos(f"Tarifa base inválida ({valor}). Debe ser mayor a 0.")
        self._tarifa_base = float(valor)

    @property
    def disponible(self) -> bool:
        """Indica si el servicio está habilitado para reservas."""
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        """Valida y actualiza el estado de disponibilidad del servicio."""
        if not isinstance(estado, bool):
            raise ErrorValidacionDatos("El estado de disponibilidad debe ser booleano (True/False).")
        self._disponible = estado

    # --- Métodos de negocio y validación ---
    def verificar_disponibilidad(self) -> None:
        """Lanza una excepción si el servicio no se encuentra disponible."""
        if not self._disponible:
            raise ErrorServicioNoDisponible(
                f"El servicio '{self._nombre}' (ID: {self.id_entidad}) no está disponible actualmente."
            )

    def validar_integridad(self) -> bool:
        """Implementación del método abstracto de EntidadSistema."""
        return bool(self._nombre and self._tarifa_base > 0)

    @abstractmethod
    def calcular_costo(self, duracion: int, impuesto: float = 0.19, descuento: float = 0.0) -> float:
        """
        Método abstracto polimórfico para calcular el costo total del servicio.
        Soporta sobrecarga mediante parámetros opcionales (impuesto y descuento).
        """
        pass

    @abstractmethod
    def describir_servicio(self) -> str:
        """Método abstracto que retorna la descripción detallada del servicio."""
        pass


class ReservaSala(Servicio):
    """
    Clase derivada que representa el servicio de alquiler de salas físicas o virtuales.
    """

    def __init__(self, id_entidad: str, nombre: str, tarifa_base: float, capacidad: int, tiene_proyector: bool = True, disponible: bool = True):
        # Llama al constructor de la clase padre Servicio
        super().__init__(id_entidad, nombre, tarifa_base, disponible)
        # Valida y asigna atributos específicos de ReservaSala
        self.capacidad = capacidad
        self.tiene_proyector = tiene_proyector
        # Registra la creación exitosa en el archivo de logs
        self._logger.registrar_evento("INFO", f"Servicio ReservaSala creado: {self.nombre} (ID: {self.id_entidad})")

    @property
    def capacidad(self) -> int:
        """Retorna el aforo máximo de personas de la sala."""
        return self._capacidad

    @capacidad.setter
    def capacidad(self, valor: int) -> None:
        """Valida que la capacidad sea un entero entre 1 y 200 personas."""
        if not isinstance(valor, int) or valor < 1 or valor > 200:
            raise ErrorValidacionDatos(f"Capacidad de sala inválida ({valor}). Debe estar entre 1 y 200.")
        self._capacidad = valor

    def calcular_costo(self, duracion: int, impuesto: float = 0.19, descuento: float = 0.0) -> float:
        """
        Calcula el costo de la sala aplicando recargo por proyector, descuento e IVA.
        """
        # Verifica que el servicio esté activo
        self.verificar_disponibilidad()
        # Valida que la duración en horas sea válida
        if not isinstance(duracion, int) or duracion <= 0:
            raise ErrorValidacionDatos("La duración de reserva de sala debe ser un entero positivo (horas).")
        if not (0 <= descuento <= 0.5):
            raise ErrorOperacionNoPermitida("El descuento permitido para salas debe estar entre 0% y 50%.")

        # Cálculo base más recargo fijo de $15.000 si incluye proyector
        recargo_equipo = 15000.0 if self.tiene_proyector else 0.0
        subtotal = (self.tarifa_base * duracion) + recargo_equipo
        # Aplica descuento e impuestos
        subtotal_con_descuento = subtotal * (1 - descuento)
        total = subtotal_con_descuento * (1 + impuesto)
        return round(total, 2)

    def describir_servicio(self) -> str:
        """Retorna descripción específica de la sala."""
        equipo = "con proyector HD" if self.tiene_proyector else "sin equipo audiovisual"
        return f"Sala '{self.nombre}' | Capacidad: {self.capacidad} personas | Equipamiento: {equipo} | Tarifa/h: ${self.tarifa_base:,.2f}"

    def obtener_resumen(self) -> str:
        """Implementación del método abstracto de EntidadSistema."""
        estado = "Disponible" if self.disponible else "No Disponible"
        return f"[{self.id_entidad}] {self.describir_servicio()} - Estado: {estado}"
