import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, Tag, Table } from 'antd';
import type { Equipment } from '../types';

const FabOverview: React.FC = () => {
    const [equipment, setEquipment] = useState<Equipment[]>([]);

    useEffect(() => {
        const fetchEquipment = async () => {
            try {
                const response = await axios.get<Equipment[]>('http://localhost:8000/api/v1/equipment');
                setEquipment(response.data);
            } catch (error) {
                console.error("Error fetching equipment:", error);
            }
        };

        fetchEquipment();
        // Poll every 5 seconds
        const interval = setInterval(fetchEquipment, 5000);
        return () => clearInterval(interval);
    }, []);

    const columns = [
        {
            title: 'Equipment ID',
            dataIndex: 'equipment_id',
            key: 'equipment_id',
        },
        {
            title: 'Type',
            dataIndex: 'type',
            key: 'type',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                let color = 'green';
                if (status === 'DOWN') color = 'red';
                if (status === 'IDLE') color = 'blue';
                if (status === 'MAINTENANCE') color = 'orange';
                return <Tag color={color}>{status}</Tag>;
            },
        },
        {
            title: 'Current Lot',
            dataIndex: 'current_lot_id',
            key: 'current_lot_id',
        },
    ];

    return (
        <Card title="Equipment Status">
            <Table dataSource={equipment} columns={columns} rowKey="equipment_id" pagination={false} />
        </Card>
    );
};

export default FabOverview;
