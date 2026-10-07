from pydantic import BaseModel, Field


class BaacSensorData(BaseModel):
    timestamp: float = Field(..., description="Timestamp de la mesure")
    lidar_distance_m: float = Field(
        ..., ge=0.0, le=200.0, description="Distance mesurée par LiDAR en mètres"
    )
    radar_velocity_kmh: float = Field(
        ..., description="Vitesse relative mesurée par radar en km/h"
    )
    brake_pressure_bar: float = Field(
        ..., ge=0.0, description="Pression de freinage appliquée (ciblé)"
    )

    # Invariant de sécurité (simplifié)
    def validate_safety_invariant(self):
        if self.lidar_distance_m < 5.0 and self.brake_pressure_bar == 0.0:
            raise ValueError(
                f"CRITICAL SAFETY INVARIANT VIOLATION: Obstacle à {self.lidar_distance_m}m sans pression de freinage !"
            )


if __name__ == "__main__":
    # Test nominal
    valid_data = BaacSensorData(
        timestamp=1723200000.0,
        lidar_distance_m=12.5,
        radar_velocity_kmh=-30.0,
        brake_pressure_bar=45.0,
    )
    print("Valid data:", valid_data)

    # Simulation d'une défaillance MLOps/Modèle
    try:
        anomaly = BaacSensorData(
            timestamp=1723200001.0,
            lidar_distance_m=3.2,
            radar_velocity_kmh=-50.0,
            brake_pressure_bar=0.0,  # Oups, le modèle n'a pas déclenché le freinage
        )
        anomaly.validate_safety_invariant()
    except ValueError as e:
        print("\n[ALERT SRE CAPTURED]", e)
