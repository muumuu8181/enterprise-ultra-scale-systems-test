export interface Lot {
  lot_id: string;
  product_id: string;
  quantity: number;
  current_step: string | null;
  status: 'WAITING' | 'PROCESSING' | 'COMPLETED' | 'HOLD';
  history: string[];
}

export interface Equipment {
  equipment_id: string;
  type: string;
  status: 'IDLE' | 'RUNNING' | 'DOWN' | 'MAINTENANCE';
  current_lot_id: string | null;
  last_maintenance: string | null;
}

export interface SPCDataPoint {
  id: number;
  xbar: number;
  r: number;
  ucl_x: number;
  lcl_x: number;
}

export interface SPCChartData {
  parameter: string;
  cpk: number;
  usl: number;
  lsl: number;
  data: SPCDataPoint[];
}
