"""
Rule Engine for Violation Detection
Implements business logic to determine violation types and severity
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger, log_violation_detected
from ..utils.config import settings

logger = get_logger(__name__)


class ViolationType(str, Enum):
    """Types of violations"""
    ENCROACHMENT = "encroachment"
    ILLEGAL_CONSTRUCTION = "illegal_construction"
    UNUSED_LAND = "unused_land"
    SUSPICIOUS_CHANGE = "suspicious_change"
    COMPLIANT = "compliant"


class Severity(str, Enum):
    """Severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectionData:
    """Container for detection data used in rule evaluation"""
    plot_id: str
    approved_area: float
    approved_land_use: str
    
    # Spatial analysis results
    has_encroachment: bool = False
    encroachment_area: float = 0.0
    encroachment_geometry: Optional[Dict] = None
    
    # ML detection results
    built_up_area: float = 0.0
    built_up_percentage: float = 0.0
    
    # Thermal analysis
    heat_signature_area: float = 0.0
    heat_percentage: float = 0.0
    mean_temperature: float = 0.0
    
    # Change detection
    change_score: float = 0.0
    has_significant_change: bool = False
    
    # Indices
    mean_ndvi: float = 0.0
    mean_ndbi: float = 0.0


@dataclass
class ViolationResult:
    """Container for violation detection result"""
    violation_type: ViolationType
    severity: Severity
    confidence: float
    description: str
    recommended_action: str
    evidence_geometry: Optional[Dict] = None
    priority: int = 3


class RuleEngine:
    """
    Rule-based decision engine for violation detection
    
    Priority hierarchy:
    1. Encroachment (activity outside boundary) - CRITICAL
    2. Illegal Construction (exceeds approved area) - HIGH
    3. Suspicious Change (rapid changes) - MEDIUM
    4. Unused Land (no activity) - LOW
    5. Compliant (within norms) - N/A
    """
    
    def __init__(self):
        """Initialize Rule Engine"""
        self.encroachment_threshold = settings.ENCROACHMENT_THRESHOLD
        self.construction_threshold = settings.ILLEGAL_CONSTRUCTION_THRESHOLD
        self.unused_threshold = settings.UNUSED_LAND_HEATMAP_THRESHOLD
        self.change_threshold = settings.CHANGE_DETECTION_THRESHOLD
    
    def evaluate(self, data: DetectionData) -> ViolationResult:
        """
        Evaluate detection data and determine violation
        
        Args:
            data: Detection data container
            
        Returns:
            ViolationResult with violation type and recommendations
        """
        logger.info(f"Evaluating rules for plot {data.plot_id}")
        
        # Priority 1: Check for encroachment
        encroachment_result = self._check_encroachment(data)
        if encroachment_result:
            log_violation_detected(
                encroachment_result.violation_type.value,
                data.plot_id,
                encroachment_result.confidence
            )
            return encroachment_result
        
        # Priority 2: Check for illegal construction
        construction_result = self._check_illegal_construction(data)
        if construction_result:
            log_violation_detected(
                construction_result.violation_type.value,
                data.plot_id,
                construction_result.confidence
            )
            return construction_result
        
        # Priority 3: Check for suspicious change
        change_result = self._check_suspicious_change(data)
        if change_result:
            log_violation_detected(
                change_result.violation_type.value,
                data.plot_id,
                change_result.confidence
            )
            return change_result
        
        # Priority 4: Check for unused land
        unused_result = self._check_unused_land(data)
        if unused_result:
            log_violation_detected(
                unused_result.violation_type.value,
                data.plot_id,
                unused_result.confidence
            )
            return unused_result
        
        # No violations - compliant
        logger.info(f"Plot {data.plot_id} is COMPLIANT")
        return self._create_compliant_result(data)
    
    def _check_encroachment(self, data: DetectionData) -> Optional[ViolationResult]:
        """
        Rule: Activity detected outside approved plot boundary
        Severity: CRITICAL (immediate action required)
        """
        if not data.has_encroachment:
            return None
        
        # Calculate encroachment percentage relative to approved area
        encroachment_pct = (data.encroachment_area / data.approved_area) * 100
        
        # Determine severity based on extent
        if encroachment_pct > 10:
            severity = Severity.CRITICAL
            priority = 1
        elif encroachment_pct > 5:
            severity = Severity.HIGH
            priority = 1
        else:
            severity = Severity.MEDIUM
            priority = 2
        
        description = (
            f"Encroachment detected: {data.encroachment_area:.2f} sqm "
            f"({encroachment_pct:.1f}% of approved area) extends beyond plot boundary. "
            f"Unauthorized use of adjacent land."
        )
        
        recommended_action = (
            f"IMMEDIATE ACTION REQUIRED:\n"
            f"1. Conduct field inspection within 24-48 hours\n"
            f"2. Issue notice to plot owner/lessee\n"
            f"3. Verify actual boundary markers on ground\n"
            f"4. Initiate encroachment removal proceedings if confirmed\n"
            f"5. Coordinate with local authorities for enforcement"
        )
        
        confidence = min(0.95, 0.80 + (encroachment_pct / 100))
        
        return ViolationResult(
            violation_type=ViolationType.ENCROACHMENT,
            severity=severity,
            confidence=confidence,
            description=description,
            recommended_action=recommended_action,
            evidence_geometry=data.encroachment_geometry,
            priority=priority
        )
    
    def _check_illegal_construction(self, data: DetectionData) -> Optional[ViolationResult]:
        """
        Rule: Built-up area exceeds approved area
        Severity: HIGH to MEDIUM
        """
        if data.built_up_area <= 0:
            return None
        
        # Calculate ratio of built-up to approved area
        construction_ratio = data.built_up_area / data.approved_area
        
        # Check if exceeds threshold (e.g., 110% of approved)
        if construction_ratio <= self.construction_threshold:
            return None
        
        excess_percentage = (construction_ratio - 1.0) * 100
        
        # Determine severity
        if excess_percentage > 50:
            severity = Severity.HIGH
            priority = 1
        elif excess_percentage > 20:
            severity = Severity.HIGH
            priority = 2
        else:
            severity = Severity.MEDIUM
            priority = 3
        
        description = (
            f"Illegal construction detected: Built-up area {data.built_up_area:.2f} sqm "
            f"exceeds approved area {data.approved_area:.2f} sqm by {excess_percentage:.1f}%. "
            f"Potential unauthorized expansion or construction."
        )
        
        recommended_action = (
            f"ACTION REQUIRED:\n"
            f"1. Schedule field verification within 1 week\n"
            f"2. Review approved building plans and permits\n"
            f"3. Measure actual built-up area on site\n"
            f"4. If confirmed, issue show-cause notice\n"
            f"5. Assess for zoning/FAR violations\n"
            f"6. Consider penalties or demolition if unapproved"
        )
        
        confidence = min(0.90, 0.70 + (excess_percentage / 200))
        
        return ViolationResult(
            violation_type=ViolationType.ILLEGAL_CONSTRUCTION,
            severity=severity,
            confidence=confidence,
            description=description,
            recommended_action=recommended_action,
            priority=priority
        )
    
    def _check_suspicious_change(self, data: DetectionData) -> Optional[ViolationResult]:
        """
        Rule: High change detection score indicates rapid alterations
        Severity: MEDIUM to LOW
        """
        if data.change_score < self.change_threshold:
            return None
        
        # Determine severity based on change score
        if data.change_score > 0.90:
            severity = Severity.MEDIUM
            priority = 2
        elif data.change_score > 0.80:
            severity = Severity.MEDIUM
            priority = 3
        else:
            severity = Severity.LOW
            priority = 4
        
        description = (
            f"Suspicious change detected: Change confidence score {data.change_score:.2%} "
            f"indicates significant alterations to the plot. "
            f"Possible unauthorized modifications or land use change."
        )
        
        recommended_action = (
            f"RECOMMENDED ACTIONS:\n"
            f"1. Review historical satellite imagery\n"
            f"2. Compare with approved development timeline\n"
            f"3. Schedule routine inspection within 2 weeks\n"
            f"4. Verify if changes align with approved plans\n"
            f"5. Check for permit applications or modifications\n"
            f"6. Monitor for further changes"
        )
        
        confidence = data.change_score
        
        return ViolationResult(
            violation_type=ViolationType.SUSPICIOUS_CHANGE,
            severity=severity,
            confidence=confidence,
            description=description,
            recommended_action=recommended_action,
            priority=priority
        )
    
    def _check_unused_land(self, data: DetectionData) -> Optional[ViolationResult]:
        """
        Rule: No built-up area AND minimal thermal signature
        Severity: LOW (monitoring/notification)
        """
        # Check for minimal activity
        has_minimal_builtup = data.built_up_percentage < 5.0
        has_minimal_heat = data.heat_percentage < self.unused_threshold * 100
        has_low_ndbi = data.mean_ndbi < 0.0  # Negative NDBI suggests vegetation/unused
        
        if not (has_minimal_builtup and has_minimal_heat):
            return None
        
        # Calculate inactivity confidence
        inactivity_score = 1.0 - (data.built_up_percentage / 100)
        
        description = (
            f"Unused land detected: Plot shows minimal activity with "
            f"only {data.built_up_percentage:.1f}% built-up area and "
            f"{data.heat_percentage:.1f}% thermal signature. "
            f"Land appears underutilized or abandoned."
        )
        
        recommended_action = (
            f"MONITORING ACTIONS:\n"
            f"1. Verify lease/allotment status and terms\n"
            f"2. Check compliance with development timeline\n"
            f"3. Send reminder notice to plot owner\n"
            f"4. Review industrial activity reports\n"
            f"5. Consider penalties for prolonged non-utilization\n"
            f"6. Evaluate for re-allotment if abandoned\n"
            f"7. Continue quarterly monitoring"
        )
        
        return ViolationResult(
            violation_type=ViolationType.UNUSED_LAND,
            severity=Severity.LOW,
            confidence=inactivity_score,
            description=description,
            recommended_action=recommended_action,
            priority=4
        )
    
    def _create_compliant_result(self, data: DetectionData) -> ViolationResult:
        """
        Create result for compliant plot (no violations)
        """
        description = (
            f"Plot is COMPLIANT: Built-up area {data.built_up_area:.2f} sqm "
            f"is within approved limits. No violations detected."
        )
        
        recommended_action = (
            f"NO ACTION REQUIRED:\n"
            f"Plot is operating within approved parameters. "
            f"Continue routine monitoring as per schedule."
        )
        
        return ViolationResult(
            violation_type=ViolationType.COMPLIANT,
            severity=Severity.LOW,
            confidence=0.85,
            description=description,
            recommended_action=recommended_action,
            priority=5
        )
    
    def batch_evaluate(
        self,
        detection_data_list: List[DetectionData]
    ) -> List[ViolationResult]:
        """
        Evaluate multiple plots in batch
        
        Args:
            detection_data_list: List of detection data
            
        Returns:
            List of violation results
        """
        results = []
        
        for data in detection_data_list:
            try:
                result = self.evaluate(data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating plot {data.plot_id}: {str(e)}")
                continue
        
        # Log summary
        violation_counts = {}
        for result in results:
            vtype = result.violation_type.value
            violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
        
        logger.info(f"Batch evaluation complete: {len(results)} plots processed")
        logger.info(f"Violation summary: {violation_counts}")
        
        return results


# Singleton instance
_rule_engine_instance = None


def get_rule_engine() -> RuleEngine:
    """
    Get or create rule engine singleton instance
    
    Returns:
        RuleEngine instance
    """
    global _rule_engine_instance
    if _rule_engine_instance is None:
        _rule_engine_instance = RuleEngine()
    return _rule_engine_instance


if __name__ == "__main__":
    # Test rule engine
    print("Testing Rule Engine...")
    
    engine = RuleEngine()
    
    # Test case 1: Encroachment
    test_data_encroachment = DetectionData(
        plot_id="TEST_001",
        approved_area=10000.0,
        approved_land_use="industrial",
        has_encroachment=True,
        encroachment_area=500.0,
        built_up_area=9500.0
    )
    
    result = engine.evaluate(test_data_encroachment)
    print(f"\nTest 1 - Encroachment:")
    print(f"  Type: {result.violation_type}")
    print(f"  Severity: {result.severity}")
    print(f"  Confidence: {result.confidence:.2%}")
    
    # Test case 2: Compliant
    test_data_compliant = DetectionData(
        plot_id="TEST_002",
        approved_area=10000.0,
        approved_land_use="industrial",
        has_encroachment=False,
        built_up_area=9000.0,
        heat_percentage=15.0
    )
    
    result = engine.evaluate(test_data_compliant)
    print(f"\nTest 2 - Compliant:")
    print(f"  Type: {result.violation_type}")
    print(f"  Confidence: {result.confidence:.2%}")
    
    print("\n✓ Rule Engine test successful")
