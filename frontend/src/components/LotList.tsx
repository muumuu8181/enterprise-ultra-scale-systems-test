import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, Table, Tag } from 'antd';
import type { Lot } from '../types';

const LotList: React.FC = () => {
    const [lots, setLots] = useState<Lot[]>([]);

    useEffect(() => {
        const fetchLots = async () => {
            try {
                const response = await axios.get<Lot[]>('http://localhost:8000/api/v1/mes/lots');
                setLots(response.data);
            } catch (error) {
                console.error("Error fetching lots:", error);
            }
        };

        fetchLots();
        // Poll every 5 seconds
        const interval = setInterval(fetchLots, 5000);
        return () => clearInterval(interval);
    }, []);

    const columns = [
        {
            title: 'Lot ID',
            dataIndex: 'lot_id',
            key: 'lot_id',
        },
        {
            title: 'Product',
            dataIndex: 'product_id',
            key: 'product_id',
        },
        {
            title: 'Quantity',
            dataIndex: 'quantity',
            key: 'quantity',
        },
        {
            title: 'Current Step',
            dataIndex: 'current_step',
            key: 'current_step',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                let color = 'blue';
                if (status === 'PROCESSING') color = 'green';
                if (status === 'HOLD') color = 'red';
                if (status === 'COMPLETED') color = 'gold';
                return <Tag color={color}>{status}</Tag>;
            }
        }
    ];

    return (
        <Card title="WIP Lots">
            <Table dataSource={lots} columns={columns} rowKey="lot_id" pagination={false} />
        </Card>
    );
};

export default LotList;
