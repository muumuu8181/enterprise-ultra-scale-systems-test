import os

class FastqProcessor:
    def __init__(self):
        pass

    def calculate_phred_score(self, quality_string):
        """Calculates the average Phred quality score for a given quality string."""
        if not quality_string:
            return 0.0

        total_score = sum(ord(char) - 33 for char in quality_string)
        return total_score / len(quality_string)

    def process_file(self, file_path):
        """
        Reads a FASTQ file and yields processed reads.
        Yields:
            tuple: (read_id, sequence, quality_string, average_quality)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break  # Real End of File

                line = line.strip()
                if not line:
                    continue  # Skip empty lines between records

                if line.startswith('@'):
                    read_id = line[1:]
                else:
                    # In standard FASTQ, ID line must start with @.
                    # If not, it's a malformed file.
                    raise ValueError(f"Invalid FASTQ format: Expected '@' at start of record, found '{line[:20]}...'")

                sequence = f.readline().strip()
                plus_line = f.readline().strip()
                quality_string = f.readline().strip()

                if not quality_string:
                    raise ValueError("Incomplete FASTQ record found.")

                avg_quality = self.calculate_phred_score(quality_string)

                yield (read_id, sequence, quality_string, avg_quality)
