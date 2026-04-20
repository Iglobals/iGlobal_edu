def single_panel_mac(root_chord, tip_chord):
    """
    Calculate MAC for one trapezoidal panel.
    Formula: MAC = (2/3) * (cr + ct - (cr*ct)/(cr+ct))
    """
    if root_chord + tip_chord == 0:
        return 0.0
    return (2.0 / 3.0) * (root_chord + tip_chord - (root_chord * tip_chord) / (root_chord + tip_chord))


def overall_wing_mac(mac_list, area_list):
    """
    Calculate the overall Mean Aerodynamic Chord for a wing made of multiple panels.
    mac_list  = list of MAC values for each panel
    area_list = list of planform areas for each panel
    (number of panels = len(mac_list) = len(area_list))
    """
    if len(mac_list) != len(area_list) or len(mac_list) == 0:
        return 0.0
    
    total_area = 0.0
    weighted_sum = 0.0
    
    for i in range(len(mac_list)):
        weighted_sum += mac_list[i] * area_list[i]
        total_area   += area_list[i]
    
    if total_area == 0.0:
        return 0.0
    return weighted_sum / total_area


# Example: Boeing 787-8 (two panels)
mac_inner = single_panel_mac(11.87, 6.42)   # ≈ 9.416 m
mac_outer = single_panel_mac(6.42, 1.69)    # ≈ 4.515 m

area_inner = 120.5   # example area in m² (you calculate from your geometry)
area_outer = 65.3    # example area in m²

overall_mac = overall_wing_mac([mac_inner, mac_outer], [area_inner, area_outer])
print("Overall MAC =", overall_mac)   # → should be ~6.27 m for the real 787