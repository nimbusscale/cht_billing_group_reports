class CostHistory:

    def __init__(self, client, perspective_id, group_id):
        self._client = client
        self._client.add_param({'dimensions[]':
                                    ['AWS-Account', 'AWS-Service-Category']})
        self._client.add_param({'measures[]': 'cost'})
        group_filter = 'Groupset-{}:select:{}'.format(perspective_id,
                                                      group_id)
        self._client.add_param({'filters[]':
                                [group_filter,
                                 'time:select:-2']})
        self._uri = 'olap_reports/cost/history'

    @property
    def raw_json(self):
        response = self._client.get(self._uri)
        return response

    def _validate_total(self, cost_lists):
        """cost_lists is a list of lists, where each list is the costs for a
        specific AWS services. The first list in cost_list is assumed to be the
        totals. _validate_total adds up all the related items in the lists and
        compares them to the expected total.

        This is used to make sure no unexpected subtotal items have been
        included by CloudHealth.

        Returns True if calculated totals match report total, otherwise False
        """
        # calculated_totals contains a list of totals for each account
        # (i.e. column in cost_lists). This line initalizes the list at 0 for
        # each account
        calculated_totals = [0 for x in cost_lists[0]]
        for cost_item in cost_lists[1:-1]:
            for column, cost in enumerate(cost_item):
                calculated_totals[column] = calculated_totals[column] + cost
        for column, total in enumerate(calculated_totals):
            report_total = cost_lists[0][column]
            if round(total, 4) != round(report_total, 4):
                return False
        return True

    @property
    def output(self):
        json = self.raw_json

        raw_columns = None
        raw_rows = None
        for dimension in json['dimensions']:
            if 'AWS-Account' in dimension.keys():
                raw_columns = [account['label'] for account in
                               dimension['AWS-Account']]
            elif 'AWS-Service-Category' in dimension.keys():
                raw_rows = [account['label'] for account in
                            dimension['AWS-Service-Category']]
        if raw_columns is None or raw_rows is None:
            exception_message = (
                "report does not include AWS-Account or AWS-Service-Category "
                "as dimensions"
            )
            raise ValueError(exception_message)
        raw_data = json['data']

        accounts = []
        accounts_cost_lists = []
        for column_number, column in enumerate(raw_columns):
            # raw_data includes a list of lists containing a single item
            # Therefore we need to compare vs the contents of the lists with
            # cost[0]
            if not all(cost[0] is None for cost in raw_data[column_number]):
                accounts.append(column)
                accounts_cost_lists.append(raw_data[column_number])

        subtotal_items = ["Amazon DynamoDB",
                          "Amazon Elastic Compute Cloud",
                          "Amazon S3 - Direct",
                          "Amazon Elastic Compute Cloud - Direct",
                          "Amazon DynamoDB - Direct"]
        accounts_csv = "Headers," + ",".join(map(str, accounts))
        report_csv = accounts_csv + "\n"
        cost_lists = []
        for row_number, row in enumerate(raw_rows):
            if row not in subtotal_items:
                cost_list = []
                for column_number, column in enumerate(accounts):
                    cost_list.append(
                        accounts_cost_lists[column_number][row_number][0]
                    )
                if not all(cost is None for cost in cost_list):
                    cost_lists.append(cost_list)
                    cost_csv = ",".join(map(str,cost_list))
                    report_csv = report_csv + "{}, {}\n".format(row, cost_csv)
        if not self._validate_total(cost_lists):
            report_csv = (
                "TOTALS DESCREPENCY DETECTED - "
                "report total does not match totals of all items. "
                "This occurs when a subtotal item has not be excluded from "
                "the report.\n" + report_csv
            )
        return report_csv
